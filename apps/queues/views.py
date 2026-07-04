import uuid
import logging
import functools
import time
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.db import transaction, IntegrityError
from .models import QueueEntry, ServiceType, Department
from apps.audit.models import AuditLog
from apps.accounts.decorators import require_permission
from apps.accounts.models import APIKey

logger = logging.getLogger(__name__)

def api_key_required(view_func):
    """Verify API key from database before allowing kiosk access."""
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        api_key = (
            request.headers.get("X-KIOSK-API-KEY") or 
            request.headers.get("X-API-Key") or 
            request.POST.get("api_key") or 
            request.GET.get("api_key")
        )
        
        if not api_key:
            logger.warning(f"Unauthorized access attempt (missing key) to {request.path} from {request.META.get('REMOTE_ADDR')}")
            AuditLog.log(
                action=AuditLog.Action.UNAUTHORIZED_ACCESS,
                user=None,
                object_type='API',
                object_id=0,
                object_name='Kiosk API',
                description=f"Missing API key attempt on {request.path}",
                request=request
            )
            return JsonResponse({"error": "Unauthorized: Missing API Key"}, status=403)
        
        try:
            # Check database for valid API key
            api_key_obj = APIKey.objects.get(key=api_key, is_active=True)
            
            # Update last_used_at timestamp
            api_key_obj.last_used_at = timezone.now()
            api_key_obj.save(update_fields=['last_used_at'])
            
            # Log successful API key use
            AuditLog.log(
                action=AuditLog.Action.API_KEY_USED,
                user=None,
                object_type='API',
                object_id=0,
                object_name=api_key_obj.name,
                description=f"API authentication successful - {request.method} {request.path}",
                request=request
            )
            
        except APIKey.DoesNotExist:
            logger.warning(f"Unauthorized access attempt (invalid key) to {request.path} from {request.META.get('REMOTE_ADDR')}")
            AuditLog.log(
                action=AuditLog.Action.UNAUTHORIZED_ACCESS,
                user=None,
                object_type='API',
                object_id=0,
                object_name='Kiosk API',
                description=f"Invalid API key attempt on {request.path}",
                request=request
            )
            return JsonResponse({"error": "Unauthorized: Invalid or inactive API Key"}, status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapper

def throttle_kiosk(view_func):
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        ip = request.META.get('REMOTE_ADDR')
        cache_key = f"throttle_kiosk_{ip}"
        count = cache.get(cache_key, 0)
        if count >= 10:  # 10 requests per minute limit
            logger.warning(f"Throttled request from {ip} on {request.path}")
            return JsonResponse({"error": "Rate limit exceeded. Try again in a minute."}, status=429)
        cache.set(cache_key, count + 1, 60)
        return view_func(request, *args, **kwargs)
    return wrapper

@csrf_exempt  # Kiosk devices don't handle CSRF tokens
@api_key_required  # Internal kiosk endpoint - API key required
@throttle_kiosk
def create_queue_entry(request):
    if request.method == "POST":
        try:
            service_type_id = request.POST.get("service_type")

            if not service_type_id:
                return JsonResponse({"error": "Missing service_type"}, status=400)

            service_type = get_object_or_404(ServiceType, id=service_type_id)
            dept = getattr(service_type, "department", None)

            retry_count = 0
            max_retries = 5

            while retry_count < max_retries:
                try:
                    with transaction.atomic():
                        # enforce per-department daily capacity if configured
                        if dept and getattr(dept, "max_entries_per_day", 0) > 0:
                            dept_count = QueueEntry.objects.filter(
                                department=dept,
                                created_at__date=timezone.now().date()
                            ).count()
                            if dept_count >= dept.max_entries_per_day:
                                logger.info(f"Capacity reached for department: {dept.name}")
                                return JsonResponse({"error": "Department capacity reached for today."}, status=429)

                        # generate number using model method (e.g., ST-0001)
                        queue_number = service_type.generate_queue_number()

                        # create entry
                        entry = QueueEntry.objects.create(
                            service_type=service_type,
                            department=dept,
                            queue_number=queue_number,
                            qr_code_data=str(uuid.uuid4()),
                        )
                        logger.info(f"New queue entry created: {entry.queue_number} for {service_type.name}")
                        
                        return JsonResponse({
                            "id": entry.id,
                            "queue_number": entry.queue_number,
                            "service_type": service_type.name,
                            "status": entry.status,
                            "created_at": entry.created_at,
                            "qr_code": entry.qr_code_data,
                        }, status=201)
                except IntegrityError:
                    retry_count += 1
                    if retry_count < max_retries:
                        sleep_time = (10 * (2 ** retry_count)) / 1000.0
                        time.sleep(sleep_time)
                        logger.debug(f"Retry attempt {retry_count}/{max_retries} for queue entry after {sleep_time*1000:.0f}ms")
                        continue
                    else:
                        logger.warning(f"Failed to create ticket after {max_retries} retries due to IntegrityError")
            
            return JsonResponse({"error": "Failed to create ticket after retries"}, status=500)

        except Exception as e:
            logger.exception(f"Error creating queue entry: {str(e)}")
            return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=405)


@csrf_exempt  # Public kiosk form - no CSRF token from kiosk devices
@throttle_kiosk
def create_queue_entry_public(request):
    """Public endpoint for kiosk form submissions - no API key required"""
    if request.method == "POST":
        try:
            import json
            
            # Handle both JSON and form-encoded data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                service_type_id = data.get("service_type_id")
                name = data.get("customer_name")
                mobile = data.get("customer_phone")
                email = data.get("customer_email")
                customer_id = data.get("customer_id")
            else:
                service_type_id = request.POST.get("service_type_id")
                name = request.POST.get("customer_name")
                mobile = request.POST.get("customer_phone")
                email = request.POST.get("customer_email")
                customer_id = request.POST.get("customer_id")

            if not service_type_id:
                return JsonResponse({"error": "Missing service_type_id"}, status=400)

            service_type = get_object_or_404(ServiceType, id=service_type_id)
            dept = service_type.department

            # Retry logic for queue number uniqueness and capacity check
            from django.db import transaction
            import time
            
            retry_count = 0
            max_retries = 5
            
            while retry_count < max_retries:
                try:
                    with transaction.atomic():
                        # Check capacity INSIDE transaction to prevent race condition
                        if dept and getattr(dept, "max_entries_per_day", 0) > 0:
                            dept_count = QueueEntry.objects.filter(
                                department=dept,
                                created_at__date=timezone.now().date()
                            ).count()
                            if dept_count >= dept.max_entries_per_day:
                                logger.info(f"Capacity reached for department: {dept.name}")
                                return JsonResponse({"error": "Department capacity reached for today."}, status=429)
                        
                        # Generate queue number using model method
                        queue_number = service_type.generate_queue_number()
                        
                        # Create entry
                        entry = QueueEntry.objects.create(
                            service_type=service_type,
                            department=dept,
                            queue_number=queue_number,
                            qr_code_data=str(uuid.uuid4()),
                            name=name,
                            mobile_number=mobile,
                            email=email,
                        )
                        
                        # Log ticket creation
                        AuditLog.log(
                            action=AuditLog.Action.TICKET_CREATED,
                            user=None,
                            object_type='QueueEntry',
                            object_id=entry.id,
                            object_name=entry.queue_number,
                            new_values={
                                'customer': name,
                                'service': service_type.name,
                                'department': dept.name if dept else 'N/A',
                            },
                            request=request
                        )
                        
                        logger.info(f"New queue entry created via public kiosk: {entry.queue_number} for {service_type.name}")
                        
                        return JsonResponse({
                            "id": entry.id,
                            "queue_number": entry.queue_number,
                            "service_type": service_type.name,
                            "ticket_number": entry.queue_number,
                            "status": entry.status,
                            "created_at": entry.created_at.isoformat(),
                            "qr_code_url": f"/queues/qr/{entry.id}/",
                        }, status=201)
                except IntegrityError:
                    retry_count += 1
                    if retry_count < max_retries:
                        # Exponential backoff: 10ms, 20ms, 40ms, 80ms
                        sleep_time = (10 * (2 ** retry_count)) / 1000.0
                        time.sleep(sleep_time)
                        logger.debug(f"Retry attempt {retry_count}/{max_retries} for queue entry after {sleep_time*1000:.0f}ms")
                        continue
                    else:
                        logger.warning(f"Failed to create ticket after {max_retries} retries due to IntegrityError")
            
            return JsonResponse({"error": "Failed to create ticket after retries"}, status=500)
        
        except ServiceType.DoesNotExist:
            return JsonResponse({"error": "Invalid service type"}, status=400)
        except Exception as e:
            logger.exception(f"Error creating public queue entry: {str(e)}")
            return JsonResponse({"error": "Internal server error"}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=405)


@login_required
@require_permission('view_tickets')
def queue_list(request):
    """List queue entries - visible to users with view_tickets permission."""
    user = request.user

    if user.has_permission('configure_system'):  # Admin check
        entries = QueueEntry.objects.exclude(status=QueueEntry.Status.SERVED).order_by("-created_at")[:10]
    else:
        entries = QueueEntry.objects.filter(
            department=user.department
        ).exclude(status=QueueEntry.Status.SERVED).order_by("-created_at")[:10]

    served_entries = QueueEntry.objects.filter(
        department=user.department if not user.has_permission('configure_system') else None,
        status=QueueEntry.Status.SERVED
    ).order_by("-served_at")[:2]

    html = render_to_string("q_queues/partials/queue_table.html", {"entries": entries}, request=request)

    return JsonResponse({
        "html": html,
        "served": [e.queue_number for e in served_entries],
        "latest_id": entries[0].id if entries else None,
    })


from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
import json

from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from .models import QueueEntry

@csrf_exempt  # kiosk/staff API
@require_http_methods(["POST", "GET"])
def update_queue_entry(request, entry_id):
    """Update queue entry status - restricted to MIS/ADMIN or kiosk API."""
    # Allow both authenticated staff AND kiosk with API key
    if request.user.is_authenticated:
        # User must have permission
        if not request.user.has_any_permission('complete_tickets', 'manage_queues'):
            logger.warning(f"Permission denied for user {request.user.username} on {request.path}")
            AuditLog.log(
                action=AuditLog.Action.PERMISSION_DENIED,
                user=request.user,
                object_type='QueueEntry',
                object_id=entry_id,
                object_name=f"QueueEntry #{entry_id}",
                request=request
            )
            return JsonResponse({"error": "Permission denied"}, status=403)
    else:
        # Check for API key in database (consistent with create_queue_entry)
        api_key = (
            request.headers.get("X-KIOSK-API-KEY") or 
            request.headers.get("X-API-Key") or 
            request.POST.get("api_key") or 
            request.GET.get("api_key")
        )
        
        is_valid_key = False
        if api_key:
            try:
                api_key_obj = APIKey.objects.get(key=api_key, is_active=True)
                is_valid_key = True
                # Update last_used_at timestamp
                api_key_obj.last_used_at = timezone.now()
                api_key_obj.save(update_fields=['last_used_at'])
            except APIKey.DoesNotExist:
                pass

        if not is_valid_key:
            logger.warning(f"Unauthorized update attempt (invalid/missing key) to {request.path} from {request.META.get('REMOTE_ADDR')}")
            AuditLog.log(
                action=AuditLog.Action.UNAUTHORIZED_ACCESS,
                user=None,
                object_type='QueueEntry',
                object_id=entry_id,
                object_name=f"QueueEntry #{entry_id}",
                description=f"Invalid API key attempt on {request.path}",
                request=request
            )
            return JsonResponse({"error": "Unauthorized: Invalid or missing API Key"}, status=403)

    entry = get_object_or_404(QueueEntry, id=entry_id)
    old_status = entry.status
    content_type = request.content_type or ''

    if request.method == "POST":
        if content_type.startswith("application/json"):
            try:
                import json
                data = json.loads(request.body)
                status = data.get("status")
            except json.JSONDecodeError:
                status = None
        else:
            status = request.POST.get("status")
    else:  # allow GET with ?status=SERVED
        status = request.GET.get("status")

    if isinstance(status, str):
        status = status.strip()

    # Normalize frontend values to backend QueueEntry statuses
    if status == "COMPLETED":
        normalized_status = QueueEntry.Status.SERVED
    else:
        normalized_status = status

    if normalized_status in dict(QueueEntry.Status.choices):
        entry.status = normalized_status
        if normalized_status == QueueEntry.Status.SERVED:
            entry.served_at = timezone.now()
        entry.save()
        logger.info(f"Queue entry {entry.queue_number} status updated from {old_status} to {status} by {request.user if request.user.is_authenticated else 'Kiosk'}")

        # Log to audit trail
        AuditLog.log(
            action=AuditLog.Action.QUEUE_ENTRY_UPDATED,
            user=request.user if request.user.is_authenticated else None,
            object_type='QueueEntry',
            object_id=entry.id,
            object_name=entry.queue_number,
            old_values={'status': old_status},
            new_values={'status': status},
            request=request
        )

        # If AJAX request
        if request.headers.get("x-requested-with", "").lower() == "xmlhttprequest" or content_type.startswith("application/json"):
            return JsonResponse({"id": entry.id, "status": entry.status})
    
    # For AJAX/JSON requests with invalid status, return error instead of redirect
    if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.content_type == "application/json":
        return JsonResponse({"error": "Invalid status", "status": status}, status=400)

    return redirect("dashboard_v4")


@login_required
def get_current_served(request):
    """Return HTML snippet for the currently served ticket info box."""
    user = request.user
    
    # Get the most recently served entry for the user's department
    if user.has_permission('configure_system'):
        # Admin sees the most recent served across all departments
        currently_served = QueueEntry.objects.filter(status=QueueEntry.Status.SERVED).order_by("-served_at").first()
    else:
        # Staff sees only the most recent served in their department
        if not user.department:
            currently_served = None
        else:
            currently_served = QueueEntry.objects.filter(
                department=user.department,
                status=QueueEntry.Status.SERVED
            ).order_by("-served_at").first()
    
    if currently_served:
        html = f"""<div class="text-muted mb-2">Currently Being Served</div>
<div class="queue-number-big text-success">{currently_served.queue_number}</div>
<div class="mt-3">
    <p><strong>Service:</strong> {currently_served.service_type.name}</p>
    <p><strong>Department:</strong> {currently_served.department.name}</p>
    <p><strong>Client Name:</strong> {currently_served.name or 'N/A'}</p>
    <p><strong>Mobile:</strong> {currently_served.mobile_number or 'N/A'}</p>
    <p><strong>Email:</strong> {currently_served.email or 'N/A'}</p>
</div>"""
    else:
        html = '<div class="text-muted text-center">No ticket currently being served</div>'
    
    return JsonResponse({"html": html}, safe=False)


@login_required
@require_permission('view_dashboard')
def dashboard(request):
    """Main queue dashboard - visible to users with view_dashboard permission."""
    user = request.user

    if user.has_permission('configure_system'):  # Admin check
        # Admin sees all departments and queues
        services = ServiceType.objects.all()
        entries = QueueEntry.objects.select_related("department").order_by("-created_at")[:10]
        served_entries = QueueEntry.objects.filter(status=QueueEntry.Status.SERVED).order_by("-served_at")[:2]
        currently_served = QueueEntry.objects.filter(status=QueueEntry.Status.SERVED).order_by("-served_at").first()
    else:
        # Staff sees only their department
        if not user.department:
            return redirect("department_selection")

        services = ServiceType.objects.filter(department=user.department)
        entries = QueueEntry.objects.filter(department=user.department).order_by("-created_at")[:10]
        served_entries = QueueEntry.objects.filter(
            department=user.department,
            status=QueueEntry.Status.SERVED
        ).order_by("-served_at")[:2]
        currently_served = QueueEntry.objects.filter(
            department=user.department,
            status=QueueEntry.Status.SERVED
        ).order_by("-served_at").first()

    return render(request, "q_queues/dashboard.html", {
        "services": services,
        "entries": entries,
        "served_entries": served_entries,
        "currently_served": currently_served,
    })


def update_status(request, entry_id, status):
    """Update queue entry status - internal function."""
    entry = get_object_or_404(QueueEntry, id=entry_id)
    entry.status = status
    if status == QueueEntry.Status.SERVED:
        from django.utils import timezone
        entry.served_at = timezone.now()
    entry.save()
    return redirect("dashboard_v4")


from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
import uuid
from .models import ServiceType, QueueEntry

from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from .models import ServiceType, QueueEntry
from .models import Department
import uuid

from django.shortcuts import redirect
from django.shortcuts import get_object_or_404, render, redirect
from .models import Department, ServiceType, QueueEntry
from django.db import IntegrityError, transaction
import uuid

def queue_ticket(request, entry_id):
    """Display ticket information to customer."""
    entry = get_object_or_404(QueueEntry, pk=entry_id)
    
    # If AJAX request, return just status
    if request.GET.get("ajax"):
        return JsonResponse({"status": entry.get_status_display()})

    # include the next 2 waiting entries for the ticket display
    now_waiting = QueueEntry.objects.filter(
        department=entry.department,
        status=QueueEntry.Status.WAITING
    ).order_by('-created_at')[:2]

    return render(request, "q_queues/ticket.html", {"entry": entry, "now_waiting": now_waiting})

def get_serving(request, entry_id):
    """Get currently serving tickets."""
    entry = get_object_or_404(QueueEntry, pk=entry_id)
    now_serving = QueueEntry.objects.filter(
        department=entry.department, status=QueueEntry.Status.SERVED
    ).order_by('-served_at')[:2]
    return render(request, "q_queues/ticket.html", {"entry": entry, "now_serving": now_serving})

@login_required
def now_serving_list(request, department_id=None):
    """List currently serving tickets."""
    qs = QueueEntry.objects.filter(status=QueueEntry.Status.SERVED)
    if not request.user.is_superuser:
        qs = qs.filter(department=request.user.department)
    elif department_id:
        qs = qs.filter(department_id=department_id)
    now_list = qs.order_by('-served_at')[:20]
    return render(request, "q_queues/now_serving.html", {"now_list": now_list})

def get_waiting(request, entry_id):
    """Get waiting queue entries."""
    entry = get_object_or_404(QueueEntry, pk=entry_id)
    now_waiting = QueueEntry.objects.filter(
        department=entry.department, status=QueueEntry.Status.WAITING
    ).order_by('-created_at')[:2]
    return render(request, "q_queues/ticket.html", {"entry": entry, "now_waiting": now_waiting})

import io
import qrcode
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.conf import settings
from .models import QueueEntry


def generate_qr(request, entry_id):
    """Generate QR code for queue ticket."""
    entry = get_object_or_404(QueueEntry, id=entry_id)

    ticket_url = request.build_absolute_uri(
        reverse("queue_ticket", args=[entry.id])
    )

    qr = qrcode.make(ticket_url)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)

    return HttpResponse(buffer.getvalue(), content_type="image/png")


from django.shortcuts import render
from apps.survey.models import SurveyResponse
from apps.queues.models import QueueEntry, ServiceType
import django.db.models as models

@login_required
@require_permission('view_reports')
def reports_dashboard(request):
    """Reports dashboard - requires view_reports permission."""
    total_queues = QueueEntry.objects.count()
    served_queues = QueueEntry.objects.filter(status=QueueEntry.Status.SERVED).count()
    avg_rating = SurveyResponse.objects.all().aggregate(models.Avg("rating"))["rating__avg"] or 0
    recent_feedbacks = SurveyResponse.objects.order_by("-created_at")[:5]

    context = {
        "total_queues": total_queues,
        "served_queues": served_queues,
        "avg_rating": round(avg_rating, 2),
        "recent_feedbacks": recent_feedbacks,
    }
    return render(request, "q_queues/reports_dashboard.html", context)


@login_required
@require_permission('configure_system')
def admin_reports_dashboard(request):
    """Admin reports dashboard - system admins only."""
    total_queues = QueueEntry.objects.count()
    served_queues = QueueEntry.objects.filter(status=QueueEntry.Status.SERVED).count()
    avg_rating = SurveyResponse.objects.all().aggregate(models.Avg("rating"))["rating__avg"] or 0
    recent_feedbacks = SurveyResponse.objects.order_by("-created_at")[:5]
    
    context = {
        "total_queues": total_queues,
        "served_queues": served_queues,
        "avg_rating": round(avg_rating, 2),
        "recent_feedbacks": recent_feedbacks,
    }
    return render(request, "q_queues/reports_dashboard.html", context)


import csv
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import QueueEntry

@login_required
@require_permission('export_data')
def export_queues_csv(request, department_id=None):
    """Export queue data to CSV - requires export_data permission."""
    if department_id and not request.user.is_superuser and request.user.department_id != int(department_id):
        AuditLog.log(
            action=AuditLog.Action.PERMISSION_DENIED,
            user=request.user,
            object_type='Export',
            object_id=department_id,
            object_name=f"Queues Export - Department {department_id}",
            request=request
        )
        return HttpResponse(status=403)
    
    # Log the export
    AuditLog.log(
        action=AuditLog.Action.EXPORT_CREATED,
        user=request.user,
        object_type='Export',
        object_id=department_id or 0,
        object_name="Queue Export CSV",
        request=request
    )
    
    qs = QueueEntry.objects.all().order_by('-created_at')
    if department_id:
        qs = qs.filter(department_id=department_id)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="queue_report.csv"'

    writer = csv.writer(response)
    writer.writerow(["Queue Number", "Service Type", "Status", "Created At", "Served At", "Name", "Email", "Mobile", "Section"])

    # Write queue data
    for q in qs:
        writer.writerow([
            q.queue_number,
            q.service_type.name if q.service_type else "",
            q.get_status_display(),
            q.created_at.strftime("%Y-%m-%d %H:%M"),
            q.served_at.strftime("%Y-%m-%d %H:%M") if q.served_at else "",
            q.name or "",
            q.email or "",
            q.mobile_number or "",
            q.section or "",
        ])

    return response

import csv
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from apps.survey.models import SurveyResponse

@login_required
@require_permission('export_data')
def export_surveys_csv(request):
    """Export survey data to CSV - requires export_data permission."""
    # Log the export
    AuditLog.log(
        action=AuditLog.Action.EXPORT_CREATED,
        user=request.user,
        object_type='Export',
        object_id=0,
        object_name="Surveys Export CSV",
        request=request
    )
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="survey_responses.csv"'

    writer = csv.writer(response)
    writer.writerow(["User", "Service Type", "Rating", "Feedback", "Created At"])

    for s in SurveyResponse.objects.all().order_by("-created_at"):
        writer.writerow([
            s.user.username if s.user else "",
            s.service_type.name if s.service_type else "",
            s.get_rating_display(),
            s.feedback,
            s.created_at.strftime("%Y-%m-%d %H:%M"),
        ])

    return response

from django.shortcuts import render
from .models import Department
from django.db.models import Count, Q
from datetime import timedelta


def department_selection(request):
    """Allow user to select their department with optimized queries."""
    from django.db.models import Count, Q, Subquery, OuterRef, Max, Prefetch
    
    # Get all departments with annotated counts - single optimized query
    # We use Prefetch to get only the latest SERVED entry to avoid loading thousands of entries
    departments = Department.objects.annotate(
        waiting_count=Count(
            'queueentry',
            filter=Q(queueentry__status=QueueEntry.Status.WAITING)
        )
    ).prefetch_related(
        Prefetch(
            'queueentry_set',
            queryset=QueueEntry.objects.filter(status=QueueEntry.Status.SERVED).order_by('-served_at'),
            to_attr='latest_served_entries'
        )
    ).all()
    
    # Process departments to add computed fields
    for dept in departments:
        serving_time = None
        currently_served = None
        
        # Get the most recent SERVED entry from prefetched data
        # Since it's ordered by -served_at, the first one is the latest
        if dept.latest_served_entries:
            serving = dept.latest_served_entries[0]
            if serving.served_at:
                time_diff = timezone.now() - serving.served_at
                serving_time = str(time_diff).split('.')[0]  # HH:MM:SS format
            currently_served = serving
        
        # Attach attributes - use annotated count for efficiency
        setattr(dept, "serving_time", serving_time)
        setattr(dept, "remaining_clients", dept.waiting_count)
        setattr(dept, "currently_served", currently_served)

    return render(request, "q_queues/department_selection.html", {"departments": departments})


try:
    from escpos.printer import Usb
except Exception:
    Usb = None

from django.template.loader import render_to_string

def print_ticket(entry):
    """Print queue ticket on thermal printer."""
    html = render_to_string("q_queues/ticket.html", {"entry": entry})
    if Usb is None:
        # escpos not available in this environment (e.g., CI or missing dependency)
        return
    try:
        printer = Usb(0x04b8, 0x0e15)
        printer.text("Queue Ticket\n\n")
        printer.text(f"Ticket No: {entry.queue_number}\n")
        printer.text(f"Department: {entry.department.name}\n")
        printer.text("-------------------------------\n")
        printer.text("Thank you for waiting!\n\n")
        printer.cut()
    except Exception:
        # printer failures shouldn't kill request flow; swallow or log in future
        pass



from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
import json

from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from .models import QueueEntry

# ============================================
# PHASE 4 DASHBOARD API ENDPOINTS
# ============================================

from django.db.models import Case, When, Avg, F

@login_required
def api_dashboard_kpi(request):
    """
    Dashboard KPI Endpoint - Real-time queue metrics
    Returns: queue_length, avg_wait_time, served_today, throughput
    """
    user = request.user
    today = timezone.now().date()
    
    if user.has_permission('configure_system'):  # Admin
        queue_qs = QueueEntry.objects.filter(status=QueueEntry.Status.WAITING)
        completed_qs = QueueEntry.objects.filter(status=QueueEntry.Status.SERVED, served_at__date=today)
        all_entries_today = QueueEntry.objects.filter(created_at__date=today)
    else:  # Staff
        if not user.department:
            return JsonResponse({"error": "No department assigned"}, status=400)
        queue_qs = QueueEntry.objects.filter(department=user.department, status=QueueEntry.Status.WAITING)
        completed_qs = QueueEntry.objects.filter(department=user.department, status=QueueEntry.Status.SERVED, served_at__date=today)
        all_entries_today = QueueEntry.objects.filter(department=user.department, created_at__date=today)
    
    queue_length = queue_qs.count()
    served_today = completed_qs.count()
    
    avg_wait = completed_qs.filter(created_at__isnull=False, served_at__isnull=False).annotate(
        wait_minutes=(F('served_at') - F('created_at'))
    ).aggregate(avg_wait=Avg('wait_minutes'))['avg_wait'] or timedelta(0)
    
    avg_wait_minutes = int(avg_wait.total_seconds() / 60) if isinstance(avg_wait, timedelta) else avg_wait
    
    total_tickets_today = all_entries_today.count()
    hours_elapsed = (timezone.now() - timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds() / 3600
    throughput = round(total_tickets_today / max(hours_elapsed, 1), 2)

    in_progress_qs = QueueEntry.objects.filter(status=QueueEntry.Status.IN_PROGRESS)
    if not user.has_permission('configure_system'):
        in_progress_qs = in_progress_qs.filter(department=user.department)
    in_progress_count = in_progress_qs.count()
    pending_count = queue_length + in_progress_count
    active_depts = all_entries_today.values('department__name').distinct().count() if user.has_permission('configure_system') else 1
    
    return JsonResponse({
        'queue_length': queue_length,
        'avg_wait_time': avg_wait_minutes,
        'served_today': served_today,
        'throughput': throughput,
        'total_today': total_tickets_today,
        'pending': pending_count,
        'active_depts': active_depts
    })


@login_required
@require_permission('view_dashboard')
def api_dashboard_charts(request):
    """
    Dashboard Charts Data - Returns 4 charts: status, department, service type, wait time trend
    """
    user = request.user
    today = timezone.now().date()
    
    if user.has_permission('configure_system'):
        queue_qs = QueueEntry.objects.all()
    else:
        if not user.department:
            return JsonResponse({"error": "No department assigned"}, status=400)
        queue_qs = QueueEntry.objects.filter(department=user.department)
    
    # 1. Queue Status Distribution
    from django.db.models import Count
    status_counts = queue_qs.values('status').annotate(count=Count('id')).order_by('-count')
    status_labels = {'WAITING': 'Waiting', 'SERVED': 'Served', 'RETURNED': 'Returned', 'CANCELLED': 'Cancelled'}
    status_data = {
        'labels': [status_labels.get(s['status'], s['status']) for s in status_counts],
        'data': [s['count'] for s in status_counts],
        'backgroundColors': ['#FF6B6B', '#4ECDC4', '#FFE66D', '#95A5A6']
    }
    
    # 2. Department Workload
    if user.has_permission('configure_system'):
        dept_counts = queue_qs.filter(created_at__date=today).values('department__name').annotate(count=Count('id')).order_by('-count')
        dept_data = {
            'labels': [d['department__name'] or 'Unassigned' for d in dept_counts],
            'data': [d['count'] for d in dept_counts],
            'backgroundColors': ['#3498DB', '#E74C3C', '#2ECC71', '#F39C12', '#9B59B6']
        }
    else:
        service_counts = queue_qs.filter(created_at__date=today).values('service_type__name').annotate(count=Count('id')).order_by('-count')
        dept_data = {
            'labels': [s['service_type__name'] for s in service_counts],
            'data': [s['count'] for s in service_counts],
            'backgroundColors': ['#3498DB', '#E74C3C', '#2ECC71', '#F39C12', '#9B59B6']
        }
    
    # 3. Service Type Distribution
    service_counts = queue_qs.filter(created_at__date=today).values('service_type__name').annotate(count=Count('id')).order_by('-count')[:5]
    service_data = {
        'labels': [s['service_type__name'] for s in service_counts],
        'data': [s['count'] for s in service_counts],
        'backgroundColors': ['#FF6B6B', '#4ECDC4', '#FFE66D', '#95E1D3', '#F38181']
    }
    
    # 4. Wait Time Trend (24-hour)
    hour_segments = []
    hour_labels = []
    for i in range(24, 0, -1):
        segment_start = timezone.now() - timedelta(hours=i)
        segment_end = timezone.now() - timedelta(hours=i-1)
        hour_label = segment_start.strftime('%H:00')
        hour_labels.append(hour_label)
        avg_wait = queue_qs.filter(created_at__gte=segment_start, created_at__lt=segment_end, served_at__isnull=False).annotate(
            wait_minutes=(F('served_at') - F('created_at'))
        ).aggregate(avg_wait=Avg('wait_minutes'))['avg_wait']
        wait_minutes = int(avg_wait.total_seconds() / 60) if isinstance(avg_wait, timedelta) else 0
        hour_segments.append(wait_minutes)
    
    trend_data = {
        'labels': hour_labels,
        'data': hour_segments,
        'borderColor': '#3498DB',
        'backgroundColor': 'rgba(52, 152, 219, 0.1)'
    }
    
    return JsonResponse({
        'status_chart': status_data,
        'department_chart': dept_data,
        'service_chart': service_data,
        'trend_chart': trend_data,
        'queue_status': status_data,
        'dept_workload': dept_data,
        'service_dist': service_data,
        'wait_trend': trend_data
    })


@login_required
@require_permission('view_dashboard')
def api_dashboard_queue(request):
    """Dashboard Active Queue - Returns list of waiting tickets"""
    user = request.user
    
    if user.has_permission('configure_system'):
        queue_qs = QueueEntry.objects.filter(status=QueueEntry.Status.WAITING).select_related('department', 'service_type').order_by('created_at')
    else:
        if not user.department:
            return JsonResponse({"error": "No department assigned"}, status=400)
        queue_qs = QueueEntry.objects.filter(department=user.department, status=QueueEntry.Status.WAITING).select_related('department', 'service_type').order_by('created_at')
    
    entries = queue_qs[:10]
    queue_data = []
    for entry in entries:
        wait_time = (timezone.now() - entry.created_at).total_seconds() / 60
        queue_data.append({
            'id': entry.id,
            'queue_number': entry.queue_number,
            'customer_name': entry.name,
            'service_type': entry.service_type.name,
            'department': entry.department.name if entry.department else 'N/A',
            'status': entry.status,
            'wait_time_minutes': int(wait_time),
            'created_at': entry.created_at.isoformat()
        })
    
    return JsonResponse({'entries': queue_data, 'queue': queue_data, 'total_waiting': queue_qs.count()})


# ============================================
# PHASE 4 ADMIN ANALYTICS API ENDPOINTS
# ============================================

@login_required
@require_permission('configure_system')
def api_admin_analytics_kpi(request):
    """Admin Analytics KPI - System-wide metrics"""
    from apps.survey.models import SurveyResponse
    
    days = request.GET.get('days', 30)
    try:
        days = int(days)
    except ValueError:
        days = 30
    
    start_date = timezone.now() - timedelta(days=days)
    ticket_qs = QueueEntry.objects.filter(created_at__gte=start_date)
    completed_tickets = ticket_qs.filter(status=QueueEntry.Status.SERVED)
    
    total_tickets = ticket_qs.count()
    completed_count = completed_tickets.count()
    completion_rate = round((completed_count / total_tickets * 100) if total_tickets > 0 else 0, 2)
    
    avg_resolution = completed_tickets.filter(created_at__isnull=False, served_at__isnull=False).annotate(
        resolution_minutes=(F('served_at') - F('created_at'))
    ).aggregate(avg_res=Avg('resolution_minutes'))['avg_res']
    
    avg_resolution_minutes = int(avg_resolution.total_seconds() / 60) if isinstance(avg_resolution, timedelta) else 0
    
    avg_satisfaction = SurveyResponse.objects.filter(created_at__gte=start_date).aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
    
    return JsonResponse({
        'total_tickets': total_tickets,
        'completion_rate': completion_rate,
        'avg_resolution_time': avg_resolution_minutes,
        'satisfaction_score': round(avg_satisfaction, 1),
        'customer_satisfaction': round(avg_satisfaction, 1)
    })


@login_required
@require_permission('configure_system')
def api_admin_analytics_charts(request):
    """Admin Analytics Charts - 6 charts with data"""
    from apps.survey.models import SurveyResponse
    from django.db.models import Count
    
    days = request.GET.get('days', 30)
    try:
        days = int(days)
    except ValueError:
        days = 30
    
    start_date = timezone.now() - timedelta(days=days)
    ticket_qs = QueueEntry.objects.filter(created_at__gte=start_date)
    
    # 1. Volume Trend
    volume_labels = []
    volume_data = []
    for i in range(days, 0, -1):
        day = (timezone.now() - timedelta(days=i)).date()
        count = ticket_qs.filter(created_at__date=day).count()
        volume_labels.append(day.strftime('%m/%d'))
        volume_data.append(count)
    
    volume_chart = {'labels': volume_labels, 'data': volume_data, 'borderColor': '#3498DB', 'backgroundColor': 'rgba(52, 152, 219, 0.1)'}
    
    # 2. Department Performance
    dept_performance = ticket_qs.values('department__name').annotate(count=Count('id')).order_by('-count')
    dept_chart = {
        'labels': [d['department__name'] or 'Unassigned' for d in dept_performance],
        'data': [d['count'] for d in dept_performance],
        'backgroundColors': ['#3498DB', '#E74C3C', '#2ECC71', '#F39C12', '#9B59B6']
    }
    
    # 3. Service Distribution
    service_dist = ticket_qs.values('service_type__name').annotate(count=Count('id')).order_by('-count')[:5]
    service_chart = {
        'labels': [s['service_type__name'] for s in service_dist],
        'data': [s['count'] for s in service_dist],
        'backgroundColors': ['#FF6B6B', '#4ECDC4', '#FFE66D', '#95E1D3', '#F38181']
    }
    
    # 4. Resolution Status
    status_dist = ticket_qs.values('status').annotate(count=Count('id'))
    status_labels = {'WAITING': 'Waiting', 'SERVED': 'Completed', 'RETURNED': 'Returned', 'CANCELLED': 'Cancelled'}
    resolution_chart = {
        'labels': [status_labels.get(s['status'], s['status']) for s in status_dist],
        'data': [s['count'] for s in status_dist],
        'backgroundColors': ['#FF6B6B', '#4ECDC4', '#FFE66D', '#95A5A6']
    }
    
    # 5. Productivity
    today = timezone.now().date()
    staff_productivity = QueueEntry.objects.filter(created_at__date=today, status=QueueEntry.Status.SERVED).values('department__name').annotate(count=Count('id')).order_by('-count')
    productivity_chart = {
        'labels': [s['department__name'] or 'Unassigned' for s in staff_productivity],
        'data': [s['count'] for s in staff_productivity],
        'borderColor': '#2ECC71',
        'backgroundColor': 'rgba(46, 204, 113, 0.1)'
    }
    
    # 6. Satisfaction Trend
    survey_data = SurveyResponse.objects.filter(created_at__gte=start_date).annotate(day=F('created_at__date')).values('day').annotate(avg_rating=Avg('rating')).order_by('day')
    satisfaction_chart = {
        'labels': [s['day'].strftime('%m/%d') for s in survey_data],
        'data': [round(s['avg_rating'], 1) for s in survey_data],
        'borderColor': '#F39C12',
        'backgroundColor': 'rgba(243, 156, 18, 0.1)'
    }
    
    return JsonResponse({
        'volume_chart': volume_chart,
        'department_chart': dept_chart,
        'service_chart': service_chart,
        'resolution_chart': resolution_chart,
        'productivity_chart': productivity_chart,
        'satisfaction_chart': satisfaction_chart
    })


@login_required
@require_permission('configure_system')
def api_admin_analytics_tables(request):
    """Admin Analytics Tables - 3 data tables"""
    from django.db.models import Count
    
    days = request.GET.get('days', 30)
    try:
        days = int(days)
    except ValueError:
        days = 30
    
    start_date = timezone.now() - timedelta(days=days)
    ticket_qs = QueueEntry.objects.filter(created_at__gte=start_date)
    
    # 1. Department Performance
    depts = Department.objects.annotate(
        total_tickets=Count(Case(When(queueentry__created_at__gte=start_date, then=1)), distinct=True),
        completed=Count(Case(When(queueentry__status=QueueEntry.Status.SERVED, queueentry__created_at__gte=start_date, then=1)), distinct=True)
    ).values('name', 'total_tickets', 'completed')
    
    dept_table = []
    for dept in depts:
        completion_rate = round((dept['completed'] / dept['total_tickets'] * 100), 1) if dept['total_tickets'] > 0 else 0
        dept_table.append({'name': dept['name'], 'total_tickets': dept['total_tickets'], 'completed': dept['completed'], 'completion_rate': completion_rate})
    
    # 2. Service Performance
    services = ServiceType.objects.annotate(
        total=Count(Case(When(queueentry__created_at__gte=start_date, then=1)), distinct=True),
        completed=Count(Case(When(queueentry__status=QueueEntry.Status.SERVED, queueentry__created_at__gte=start_date, then=1)), distinct=True)
    ).values('name', 'total', 'completed').filter(total__gt=0)
    
    service_table = []
    for service in services:
        completion_rate = round((service['completed'] / service['total'] * 100), 1) if service['total'] > 0 else 0
        service_table.append({'name': service['name'], 'total': service['total'], 'completed': service['completed'], 'completion_rate': completion_rate})
    
    # 3. Staff Performance
    staff_table = ticket_qs.values('department__name').annotate(
        tickets_served=Count(Case(When(status=QueueEntry.Status.SERVED, then=1))),
        avg_wait_time=Avg(Case(When(served_at__isnull=False, then=(F('served_at') - F('created_at'))), output_field=models.DurationField()))
    )
    
    staff_perf_table = []
    for staff in staff_table:
        avg_wait = staff['avg_wait_time']
        avg_wait_minutes = int(avg_wait.total_seconds() / 60) if isinstance(avg_wait, timedelta) else 0
        staff_perf_table.append({'name': staff['department__name'] or 'Unassigned', 'tickets_served': staff['tickets_served'], 'avg_wait_time': avg_wait_minutes})
    
    return JsonResponse({
        'departments': dept_table,
        'services': service_table,
        'staff': staff_perf_table
    })


@login_required
@require_permission('configure_system')
def api_admin_analytics_audit(request):
    """Admin Analytics Audit Trail"""
    from apps.audit.models import AuditLog
    
    limit = request.GET.get('limit', 50)
    try:
        limit = int(limit)
    except ValueError:
        limit = 50
    
    audit_entries = AuditLog.objects.select_related('user').order_by('-timestamp')[:limit]
    
    audit_data = []
    for entry in audit_entries:
        audit_data.append({
            'id': entry.id,
            'timestamp': entry.timestamp.isoformat(),
            'user': entry.user.username if entry.user else 'System',
            'action': entry.get_action_display(),
            'object_type': entry.object_type,
            'object_name': entry.object_name,
            'description': entry.description
        })
    
    return JsonResponse({'audit_trail': audit_data, 'total_entries': AuditLog.objects.count()})


# ============================================
# VIEW HANDLERS FOR TEMPLATES
# ============================================

@login_required
@require_permission('view_dashboard')
def dashboard_v4(request):
    """Enhanced Staff Dashboard v4"""
    user = request.user
    
    # Non-admin users must have a department assigned
    if not user.has_permission('configure_system') and not user.department:
        return redirect('department_selection')
    
    context = {
        'user': user,
        'department': user.department if not user.has_permission('configure_system') else None,
        'departments': Department.objects.all() if user.has_permission('configure_system') else [user.department],
        'is_admin': user.has_permission('configure_system'),
    }
    return render(request, 'q_queues/dashboard_v4.html', context)



def kiosk_v4(request):
    """Enhanced Kiosk v4 - Multi-step form"""
    import json
    
    departments = Department.objects.all()
    service_types = ServiceType.objects.all()
    
    # Create Python dicts for JSON serialization
    departments_data = [{'id': d.id, 'name': d.name} for d in departments]
    service_types_data = [{'id': s.id, 'name': s.name, 'department_id': s.department_id} for s in service_types]
    
    # Convert to JSON strings for safe template rendering
    departments_json = json.dumps(departments_data)
    service_types_json = json.dumps(service_types_data)
    
    context = {
        'departments': departments,
        'service_types': service_types,
        'departments_json': departments_json,
        'service_types_json': service_types_json,
    }
    return render(request, 'q_queues/kiosk_v4.html', context)


@login_required
@require_permission('configure_system')
def admin_analytics(request):
    """Admin Analytics Dashboard v4"""
    context = {
        'user': request.user,
        'departments': Department.objects.all(),
        'service_types': ServiceType.objects.all(),
        'default_days': 30,
    }
    return render(request, 'admin/analytics_dashboard.html', context)


def api_get_services(request):
    """Get services by department (for kiosk step 1) - Public API"""
    from django.db.models import Count
    dept_id = request.GET.get('department_id')
    
    if not dept_id:
        return JsonResponse({'error': 'Missing department_id'}, status=400)
    
    services = ServiceType.objects.filter(department_id=dept_id).values('id', 'name', 'description')
    return JsonResponse(list(services), safe=False)
