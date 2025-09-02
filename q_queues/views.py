import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import QueueEntry, ServiceType

@csrf_exempt  # Kiosk devices don’t handle CSRF tokens
def create_queue_entry(request):
    if request.method == "POST":
        # kiosk sends which service type
        service_type_id = request.POST.get("service_type")

        if not service_type_id:
            return JsonResponse({"error": "Missing service_type"}, status=400)

        service_type = get_object_or_404(ServiceType, id=service_type_id)

        # generate queue number (e.g., ST-001)
        count_today = QueueEntry.objects.filter(
            service_type=service_type,
            created_at__date=timezone.now().date()
        ).count() + 1

        queue_number = f"{service_type.name[:2].upper()}-{count_today:03d}"

        # create entry
        entry = QueueEntry.objects.create(
            service_type=service_type,
            queue_number=queue_number,
            qr_code_data=str(uuid.uuid4()),  # unique QR
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

from django.http import JsonResponse
from .models import QueueEntry

def queue_list(request):
    # Only show waiting queues
    entries = QueueEntry.objects.filter(status=QueueEntry.Status.WAITING).order_by("created_at")

    data = [
        {
            "id": e.id,
            "queue_number": e.queue_number,
            "service_type": e.service_type.name,
            "status": e.status,
            "created_at": e.created_at,
        }
        for e in entries
    ]

    return JsonResponse(data, safe=False)
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
import json

@csrf_exempt  # kiosk/staff API, you can add auth later
@require_http_methods(["POST"])
def update_queue_entry(request, entry_id):
    try:
        entry = QueueEntry.objects.get(id=entry_id)
    except QueueEntry.DoesNotExist:
        return JsonResponse({"error": "Queue entry not found"}, status=404)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    new_status = data.get("status")
    valid_statuses = [choice[0] for choice in QueueEntry.Status.choices]

    if new_status not in valid_statuses:
        return JsonResponse({"error": "Invalid status"}, status=400)

    entry.status = new_status
    if new_status == QueueEntry.Status.SERVED:
        entry.served_at = timezone.now()
    entry.save()

    return JsonResponse({
        "id": entry.id,
        "queue_number": entry.queue_number,
        "status": entry.status,
        "served_at": entry.served_at
    })

from django.shortcuts import render
from .models import QueueEntry, ServiceType

def queue_dashboard(request):
    services = ServiceType.objects.all()
    entries = QueueEntry.objects.select_related("service_type").order_by("-created_at")[:20]
    return render(request, "queues/dashboard.html", {
        "services": services,
        "entries": entries
    })
