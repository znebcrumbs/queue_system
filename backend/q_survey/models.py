from django.db import models
from django.utils import timezone
from q_accounts.models import User

class SurveyResponse(models.Model):
    class Rating(models.IntegerChoices):
        VERY_POOR = 1, "Very Poor"
        POOR = 2, "Poor"
        AVERAGE = 3, "Average"
        GOOD = 4, "Good"
        EXCELLENT = 5, "Excellent"

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    service_type = models.ForeignKey(
        "q_queues.ServiceType",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    queues_entry = models.OneToOneField(
        "q_queues.QueueEntry",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    rating = models.IntegerField(choices=Rating.choices)
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Survey {self.id} - {self.rating}★"

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Survey {self.id} by {self.user.username} - {self.rating}★"

    class Meta:
        ordering = ["-created_at"]
