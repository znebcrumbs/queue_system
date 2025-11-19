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
    department = data.get("department")

    try:
        queue_entry = QueueEntry.objects.get(id=queue_id)
    except QueueEntry.DoesNotExist:
        return JsonResponse({"error": "Queue entry not found"}, status=404)

    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return JsonResponse({"error": "Rating must be 1–5"}, status=400)

    survey = SurveyResponse.objects.create(
        user="Anon",
        service_type=queue_entry.service_type,
        queues_entry=queue_entry,
        rating=rating,
        feedback=feedback,
        department=department
    )

    return JsonResponse({
        "id": survey.id,
        "queue_entry": queue_entry.queue_number,
        "service_type": queue_entry.service_type.name,
        "rating": survey.rating,
        "feedback": survey.feedback,
        "created_at": survey.created_at,
    }, status=201)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import SurveyResponse
from q_queues.models import QueueEntry 
from q_queues.models import Department

def survey_view(request, entry_id):
    entry = get_object_or_404(QueueEntry, id=entry_id)

    questions = [
        ("registration_ease", "How easy was it to register and get a queue number?"),
        ("system_usability", "Was the kiosk/web system interface user-friendly?"),
        ("realtime_updates", "Were the real-time queue updates clear and helpful?"),
        ("waiting_time_accuracy", "How would you rate the estimated waiting time displayed?"),
        ("waiting_time_satisfaction", "How satisfied are you with the waiting time before being served?"),
        ("staff_professionalism", "How would you rate the staff’s courtesy and professionalism?"),
        ("overall_satisfaction", "How satisfied are you with the overall service provided?")
    ]

    if request.method == "POST":
        data = {
            "user": request.user,
            "service_type": entry.service_type,
            "queues_entry": entry,
            "feedback": request.POST.get("feedback", ""),
            "rating": request.POST.get("overall_satisfaction")  # treat overall as main rating
        }

        for field, _ in questions:
            value = request.POST.get(field)
            if value:
                data[field] = value

        SurveyResponse.objects.create(**data)
        messages.success(request, "Thank you for your feedback!")
        return redirect("queue_ticket", entry_id=entry.id)

    return render(request, "q_survey/survey_form.html", {
        "entry": entry,
        "rating_choices": SurveyResponse.Rating.choices,
        "questions": questions,   # pass list into template
    })