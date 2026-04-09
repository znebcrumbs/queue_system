from django.db import models
from django.utils import timezone
from apps.accounts.models import User

class SurveyResponse(models.Model): 
    class Rating(models.IntegerChoices):
        VERY_POOR = 1, "Very Poor"
        POOR = 2, "Poor"
        AVERAGE = 3, "Average"
        GOOD = 4, "Good"
        EXCELLENT = 5, "Excellent"

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service_type = models.ForeignKey("queues.ServiceType", on_delete=models.SET_NULL, null=True, blank=True)
    queues_entry = models.OneToOneField("queues.QueueEntry", on_delete=models.CASCADE, null=True, blank=True)

   
    rating = models.IntegerField(choices=Rating.choices)
    feedback = models.TextField(blank=True)


    department = models.CharField(max_length=100, blank=True, null=True)
    purpose =  models.CharField(max_length=100, blank=True, null=True)

    registration_ease = models.IntegerField(choices=Rating.choices, null=True, blank=True)
    system_usability = models.IntegerField(choices=Rating.choices, null=True, blank=True)
    realtime_updates = models.IntegerField(choices=Rating.choices, null=True, blank=True)
    waiting_time_accuracy = models.IntegerField(choices=Rating.choices, null=True, blank=True)
    waiting_time_satisfaction = models.IntegerField(choices=Rating.choices, null=True, blank=True)
    staff_professionalism = models.IntegerField(choices=Rating.choices, null=True, blank=True)
    overall_satisfaction = models.IntegerField(choices=Rating.choices, null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Survey {self.id} by {self.user.username} - {self.rating}★"

    class Meta:
        ordering = ["-created_at"]
