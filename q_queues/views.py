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

        # generate number (e.g., ST-001), if guba ang ticket icheck ni
        count_today = QueueEntry.objects.filter(
            service_type=service_type,
            created_at__date=timezone.now().date()
        ).count() + 1

        queue_number = f"{service_type.name[:2].upper()}-{count_today:03d}"

        # create entry sa ano
        entry = QueueEntry.objects.create(
            service_type=service_type,
            queue_number=queue_number,
            qr_code_data=str(uuid.uuid4()),  # pampa unique sa qr 
        )

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

    if user.role == "ADMIN":
        entries = QueueEntry.objects.exclude(status=QueueEntry.Status.SERVED).order_by("-created_at")[:10]
    else:
        entries = QueueEntry.objects.filter(
            service_type__assigned_role=user.role
        ).exclude(status=QueueEntry.Status.SERVED).order_by("-created_at")[:10]

    # latest 2 served queues
    served_entries = QueueEntry.objects.filter(
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
def dashboard(request):
    user = request.user

    # Admin → see all
    if user.role == "ADMIN":
        services = ServiceType.objects.all()
        entries = QueueEntry.objects.order_by("-created_at")[:10]

    # Staff → filter by assigned_role
    else:
        services = ServiceType.objects.filter(assigned_role=user.role)
        entries = QueueEntry.objects.filter(
            service_type__assigned_role=user.role
        ).order_by("-created_at")[:10]

    served_entries = QueueEntry.objects.filter(
        status=QueueEntry.Status.SERVED,
        service_type__assigned_role=user.role if user.role != "ADMIN" else None
    ).order_by("-served_at")[:2]

    return render(request, "q_queues/dashboard.html", {
        "services": services,
        "entries": entries,
        "served_entries": served_entries,
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
import uuid

from django.shortcuts import redirect

def kiosk(request):
    if request.method == "POST":
        service_id = request.POST.get("service_type")
        name = request.POST.get("name")
        mobile = request.POST.get("mobile_number")
        email = request.POST.get("email")
        section = request.POST.get("section")

        service = get_object_or_404(ServiceType, id=service_id)

        for _ in range(3):
            try:
                with transaction.atomic():
                    queue_number = service.generate_queue_number()
                    entry = QueueEntry.objects.create(
                        service_type=service,
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

        return JsonResponse({"error": "Ultra Super Rare Error, Show this to the cashier to get a free discount!"}, status=500)

    services = ServiceType.objects.all()
    return render(request, "q_queues/kiosk.html", {"services": services})



def queue_ticket(request, entry_id):
    entry = get_object_or_404(QueueEntry, pk=entry_id)

    # If AJAX request, return just status para sure kay galibog na ko
    if request.GET.get("ajax"):
        return JsonResponse({"status": entry.get_status_display()})

    return render(request, "q_queues/ticket.html", {"entry": entry})


from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.urls import reverse
import qrcode
import io

def generate_qr(request, entry_id):
    entry = get_object_or_404(QueueEntry, id=entry_id)
    
    # 
    ticket_url = request.build_absolute_uri(reverse("queue_ticket", args=[entry.id]))
    
    # 
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    
    return HttpResponse(buffer.getvalue(), content_type="image/png")

# q_queues/views.py (add near other imports)
from django.shortcuts import render
from django.db.models import Count, Avg, F, DurationField, ExpressionWrapper
from django.db.models.functions import ExtractHour
from django.http import HttpResponse
import csv
from datetime import date, timedelta

# assume QueueEntry and ServiceType are already imported in this file
# from .models import QueueEntry, ServiceType

# Reports dashboard
def reports_dashboard(request):
    today = date.today()
    week_start = today - timedelta(days=7)

    # General counts
    total_today = QueueEntry.objects.filter(created_at__date=today).count()
    served_today = QueueEntry.objects.filter(created_at__date=today, status=QueueEntry.Status.SERVED).count()
    total_week = QueueEntry.objects.filter(created_at__date__gte=week_start).count()

    # Average waiting time (served entries): served_at - created_at
    served_qs = QueueEntry.objects.filter(status=QueueEntry.Status.SERVED, served_at__isnull=False)
    # expression for duration in seconds
    wait_expr = ExpressionWrapper(F('served_at') - F('created_at'), output_field=DurationField())
    avg_wait = served_qs.annotate(wait_time=wait_expr).aggregate(avg_wait=Avg('wait_time'))['avg_wait']

    # service-level stats: number served and avg wait per service (last 7 days)
    service_stats_qs = (
        served_qs.filter(created_at__date__gte=week_start)
        .values('service_type__id', 'service_type__name')
        .annotate(served_count=Count('id'), avg_wait=Avg(wait_expr))
        .order_by('-served_count')
    )

    # peak hours (from all entries created in last 7 days)
    peak_qs = (
        QueueEntry.objects.filter(created_at__date__gte=week_start)
        .annotate(hour=ExtractHour('created_at'))
        .values('hour')
        .annotate(cnt=Count('id'))
        .order_by('-cnt')
    )
    # convert to arrays for charts
    hours = [r['hour'] for r in peak_qs]
    hour_counts = [r['cnt'] for r in peak_qs]

    # Surveys (if q_survey is installed)
    try:
        from q_survey.models import SurveyResponse
        avg_rating = SurveyResponse.objects.aggregate(avg=Avg('rating'))['avg'] or 0
        rating_dist_qs = SurveyResponse.objects.values('rating').annotate(cnt=Count('id')).order_by('rating')
        rating_labels = [r['rating'] for r in rating_dist_qs]
        rating_counts = [r['cnt'] for r in rating_dist_qs]
        recent_feedbacks = SurveyResponse.objects.filter(feedback__gt="").order_by('-created_at')[:10]
    except Exception:
        avg_rating = 0
        rating_labels = []
        rating_counts = []
        recent_feedbacks = []

    context = {
        'total_today': total_today,
        'served_today': served_today,
        'total_week': total_week,
        'avg_wait': avg_wait,
        'service_stats': list(service_stats_qs),
        'peak_hours': hours,
        'peak_counts': hour_counts,
        'avg_rating': avg_rating,
        'rating_labels': rating_labels,
        'rating_counts': rating_counts,
        'recent_feedbacks': recent_feedbacks,
    }
    return render(request, "q_queues/reports_dashboard.html", context)


# CSV exports
def export_queues_csv(request):
    qs = QueueEntry.objects.order_by('-created_at').all()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="queues.csv"'

    writer = csv.writer(response)
    writer.writerow(['id', 'queue_number', 'service_type', 'status', 'client', 'created_at', 'served_at', 'qr_code_data'])
    for e in qs:
        writer.writerow([
            e.id,
            e.queue_number,
            e.service_type.name if e.service_type else '',
            e.status,
            (e.client.username if e.client else ''),
            e.created_at.isoformat() if e.created_at else '',
            e.served_at.isoformat() if e.served_at else '',
            e.qr_code_data or '',
        ])
    return response


def export_surveys_csv(request):
    try:
        from q_survey.models import SurveyResponse
    except Exception:
        return HttpResponse("Survey app not installed", status=404)

    qs = SurveyResponse.objects.order_by('-created_at').all()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="surveys.csv"'

    writer = csv.writer(response)
    writer.writerow(['id', 'user', 'service_type', 'queue_number', 'rating', 'feedback', 'created_at'])
    for s in qs:
        writer.writerow([
            s.id,
            s.user.username if s.user else '',
            s.service_type.name if s.service_type else '',
            s.queues_entry.queue_number if s.queues_entry else '',
            s.rating,
            s.feedback,
            s.created_at.isoformat(),
        ])
    return response
