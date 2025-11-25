import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import QueueEntry, ServiceType

@csrf_exempt  # dapat Kiosk devices don’t handle CSRF tokens
def create_queue_entry(request):
    if request.method == "POST":
        # ang kay kiosk send ug service type pero depende ra sa akong ka pogi
        service_type_id = request.POST.get("service_type")

        if not service_type_id:
            return JsonResponse({"error": "Missing service_type"}, status=400)

        service_type = get_object_or_404(ServiceType, id=service_type_id)

        # enforce per-department daily capacity if configured
        dept = getattr(service_type, "department", None)
        if dept and getattr(dept, "max_entries_per_day", 0) > 0:
            dept_count = QueueEntry.objects.filter(
                department=dept,
                created_at__date=timezone.now().date()
            ).count()
            if dept_count >= dept.max_entries_per_day:
                return JsonResponse({"error": "Department capacity reached for today."}, status=429)

        # generate number (e.g., ST-001), if guba ang ticket icheck ni
        count_today = QueueEntry.objects.filter(
            service_type=service_type,
            created_at__date=timezone.now().date()
        ).count() + 1

        queue_number = f"{service_type.name[:2].upper()}-{count_today:03d}"

        # create entry sa ano
        entry = QueueEntry.objects.create(
            service_type=service_type,
            department=dept,
            queue_number=queue_number,
            qr_code_data=str(uuid.uuid4()),  # pampa unique sa qr 
        )
        entry.save()
        print_ticket(entry)
        return JsonResponse({
            "id": entry.id,
            "queue_number": entry.queue_number,
            "service_type": service_type.name,
            "status": entry.status,
            "created_at": entry.created_at,
            "qr_code": entry.qr_code_data,
        }, status=201)

    return JsonResponse({"error": "Invalid request"}, status=405)


from django.template.loader import render_to_string
from django.http import JsonResponse
from .models import QueueEntry

from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required


@login_required
def queue_list(request):
    user = request.user

    if user.role == "Administrator":
        entries = QueueEntry.objects.exclude(status=QueueEntry.Status.SERVED).order_by("-created_at")[:10]
    else:
        entries = QueueEntry.objects.filter(
            department=user.department
        ).exclude(status=QueueEntry.Status.SERVED).order_by("-created_at")[:10]

    served_entries = QueueEntry.objects.filter(
        department=user.department if user.role != "Administrator" or "admin" else None,
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
@csrf_exempt  # kiosk/staff API, I SHOULD add auth later
@require_http_methods(["POST"])


def update_queue_entry(request, entry_id):
    entry = get_object_or_404(QueueEntry, id=entry_id)

    if request.method == "POST":
        status = request.POST.get("status")
    else:  # allow GET with ?status=SERVED
        status = request.GET.get("status")

    if status in dict(QueueEntry.Status.choices):
        entry.status = status
        if status == QueueEntry.Status.SERVED:
            from django.utils import timezone
            entry.served_at = timezone.now()
        entry.save()

        # If AJAX request
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"id": entry.id, "status": entry.status})

    return redirect("dashboard")


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import QueueEntry, ServiceType

@login_required
def get_current_served(request):
    """Return HTML snippet for the currently served ticket info box."""
    user = request.user
    
    # Get the most recently served entry for the user's department
    if user.role == "ADMIN":
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
def dashboard(request):
    user = request.user

    if user.role == "ADMIN":
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


from django.shortcuts import render, redirect, get_object_or_404

def update_status(request, entry_id, status):
    entry = get_object_or_404(QueueEntry, id=entry_id)
    entry.status = status
    if status == QueueEntry.Status.SERVED:
        from django.utils import timezone
        entry.served_at = timezone.now()
    entry.save()
    return redirect("dashboard")


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

def kiosk(request, department_slug=None):
    department = None
    if department_slug:
        department = get_object_or_404(Department, name=department_slug)
    if request.method == "POST":
        service_id = request.POST.get("service_type")
        name = request.POST.get("name")
        mobile = request.POST.get("mobile_number")
        email = request.POST.get("email")
        section = request.POST.get("section")
        dept_id = request.POST.get("department")

        selected_department = get_object_or_404(Department, name=department_slug)
        service = get_object_or_404(ServiceType, id=service_id)

        # enforce per-department daily capacity if configured
        if selected_department and getattr(selected_department, "max_entries_per_day", 0) > 0:
            today_count = QueueEntry.objects.filter(
                department=selected_department,
                created_at__date=timezone.now().date()
            ).count()
            if today_count >= selected_department.max_entries_per_day:
                services = ServiceType.objects.filter(department=selected_department)
                departments = Department.objects.all()
                return render(request, "q_queues/kiosk.html", {
                    "services": services,
                    "departments": departments,
                    "selected_department": selected_department,
                    "error": "Department capacity reached for today.",
                })

        for _ in range(3):
            try:
                with transaction.atomic():
                    queue_number = service.generate_queue_number()
                    entry = QueueEntry.objects.create(
                        service_type=service,
                        department=selected_department,
                        queue_number=queue_number,
                        qr_code_data=str(uuid.uuid4()),
                        name=name,
                        mobile_number=mobile,
                        email=email,
                        section=section,
                    )
                return redirect("queue_ticket", entry_id=entry.id)
            except IntegrityError:
                continue

        return JsonResponse({"error": "Failed to create ticket. Please try again."}, status=500)

    services = ServiceType.objects.filter(department=department)
    departments = Department.objects.all()
    return render(request, "q_queues/kiosk.html", {
        "services": services,
        "departments": departments,
        "selected_department": department,
    })

def queue_ticket(request, entry_id):
    entry = get_object_or_404(QueueEntry, pk=entry_id)
    
    # If AJAX request, return just status para sure kay galibog na ko
   
    if request.GET.get("ajax"):
        return JsonResponse({"status": entry.get_status_display()})

    # include the next 2 waiting entries for the ticket display
    now_waiting = QueueEntry.objects.filter(
        department=entry.department,
        status=QueueEntry.Status.WAITING
    ).order_by('-created_at')[:2]

    return render(request, "q_queues/ticket.html", {"entry": entry, "now_waiting": now_waiting})

def get_serving(request, entry_id):
    entry = get_object_or_404(QueueEntry, pk=entry_id)
    now_serving = QueueEntry.objects.filter(
        department=entry.department, status=QueueEntry.Status.SERVED
    ).order_by('-served_at')[:2]  # or filter status="SERVING" if you have such state
    return render(request, "q_queues/ticket.html", {"entry": entry, "now_serving": now_serving})

@login_required
def now_serving_list(request, department_id=None):
    qs = QueueEntry.objects.filter(status=QueueEntry.Status.SERVED)
    if not request.user.is_superuser:
        qs = qs.filter(department=request.user.department)
    elif department_id:
        qs = qs.filter(department_id=department_id)
    now_list = qs.order_by('-served_at')[:20]
    return render(request, "q_queues/now_serving.html", {"now_list": now_list})

def get_waiting(request, entry_id):
    entry = get_object_or_404(QueueEntry, pk=entry_id)
    now_waiting = QueueEntry.objects.filter(
        department=entry.department, status=QueueEntry.Status.WAITING
    ).order_by('-created_at')[:2]  # or filter status="SERVING" if you have such state
    return render(request, "q_queues/ticket.html", {"entry": entry, "now_waiting": now_waiting})

import io
import qrcode
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.conf import settings
from .models import QueueEntry


def generate_qr(request, entry_id):
    entry = get_object_or_404(QueueEntry, id=entry_id)

    ticket_url = request.build_absolute_uri(
        reverse("queue_ticket", args=[entry.id])
    )

    
    qr = qrcode.make(ticket_url)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)

    return HttpResponse(buffer.getvalue(), content_type="image/png")
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from q_survey.models import SurveyResponse
from q_queues.models import QueueEntry, ServiceType
import django.db.models as models

@login_required
def reports_dashboard(request):
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

# q_queues/views.py
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_reports_dashboard(request):
    total_queues = QueueEntry.objects.count()
    served_queues = QueueEntry.objects.filter(status=QueueEntry.Status.SERVED).count()
    avg_rating = SurveyResponse.objects.all().aggregate(models.Avg("rating"))["rating__avg"] or 0
    recent_feedbacks = SurveyResponse.objects.order_by("-created_at")[:5]
    return reports_dashboard(request)


import csv
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import QueueEntry

@login_required
def export_queues_csv(request, department_id=None):
    if not request.user.is_superuser and department_id and request.user.department_id != int(department_id):
        return HttpResponse(status=403)
    qs = QueueEntry.objects.all().order_by('-created_at')
    if department_id:
        qs = qs.filter(department_id=department_id)
    # rest of CSV writer as before...
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="queue_report.csv"'

    writer = csv.writer(response)
    writer.writerow(["Queue Number", "Service Type", "Status", "Created At", "Served At", "Name", "Email", "Mobile", "Section"])

    # Write queue data
    for q in QueueEntry.objects.all().order_by("-created_at"):
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
from q_survey.models import SurveyResponse

@login_required
def export_surveys_csv(request):
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
    departments = Department.objects.all()
    for dept in departments:
        # Get currently serving entry (status SERVED, most recent)
        serving = QueueEntry.objects.filter(
            department=dept,
            status=QueueEntry.Status.SERVED
        ).order_by('-served_at').first()

        serving_time = None
        if serving and serving.served_at:
            time_diff = timezone.now() - serving.served_at
            serving_time = str(time_diff).split('.')[0]  # HH:MM:SS format

        # Count remaining waiting clients
        remaining_count = QueueEntry.objects.filter(
            department=dept,
            status=QueueEntry.Status.WAITING
        ).count()

        # attach attributes directly so template can access them on the object
        setattr(dept, "serving_time", serving_time)
        setattr(dept, "remaining_clients", remaining_count)
        setattr(dept, "currently_served", serving)

    return render(request, "q_queues/department_selection.html", {"departments": departments})



try:
    from escpos.printer import Usb
except Exception:
    Usb = None

from django.template.loader import render_to_string

def print_ticket(entry):
    html = render_to_string("q_queues/ticket.html", {"entry": entry})
    if Usb is None:
        # escpos not available in this environment (e.g., CI or missing dependency)
        return
    try:
        printer = Usb(0x04b8, 0x0e15)  # para as printer
        printer.text("Queue Ticket\n\n")
        printer.text(f"Ticket No: {entry.queue_number}\n")
        printer.text(f"Department: {entry.department.name}\n")
        printer.text("-------------------------------\n")
        printer.text("Thank you for waiting!\n\n")
        printer.cut()
    except Exception:
        # printer failures shouldn't kill request flow; swallow or log in future
        pass

