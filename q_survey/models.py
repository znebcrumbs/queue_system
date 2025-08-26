from django.db import models
from q_queues.models import QueueEntry

class SurveyResponse(models.Model):
    queue_entry = models.OneToOneField(QueueEntry, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()  # 1-5
    comments = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Survey for {self.queue_entry.queue_number} - {self.rating}/5"
