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



import qrcode
from django.http import HttpResponse
import io
def generate_qr(request, entry_id):
    entry = get_object_or_404(QueueEntry, id=entry_id)
    qr = qrcode.make(entry.qr_code_data)  # ✅ use the correct field
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type="image/png")


