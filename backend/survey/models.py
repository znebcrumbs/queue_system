from django.db import models
from queue.models import QueueEntry

class SurveyResponse(models.Model):
    queue_entry = models.OneToOneField(QueueEntry, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()  # 1-5 scale
    comments = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Survey for {self.queue_entry.queue_number} - {self.rating}/5"
