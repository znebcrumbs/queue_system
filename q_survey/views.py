from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import SurveyResponse
from q_queues.models import QueueEntry

def survey_list(request):
    surveys = SurveyResponse.objects.all().values(
        "id", "user__username", "rating", "feedback", "created_at"
    )
    return JsonResponse(list(surveys), safe=False)


@csrf_exempt
@require_http_methods(["POST"])
def submit_survey(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    queue_id = data.get("queue_entry")
    rating = data.get("rating")
    feedback = data.get("feedback", "")

    try:
        queue_entry = QueueEntry.objects.get(id=queue_id)
    except QueueEntry.DoesNotExist:
        return JsonResponse({"error": "Queue entry not found"}, status=404)

    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return JsonResponse({"error": "Rating must be 1–5"}, status=400)

    survey = SurveyResponse.objects.create(
        user=queue_entry.client,
        service_type=queue_entry.service_type,
        queues_entry=queue_entry,
        rating=rating,
        feedback=feedback,
    )

    return JsonResponse({
        "id": survey.id,
        "queue_entry": queue_entry.queue_number,
        "service_type": queue_entry.service_type.name,
        "rating": survey.rating,
        "feedback": survey.feedback,
        "created_at": survey.created_at,
    }, status=201)
