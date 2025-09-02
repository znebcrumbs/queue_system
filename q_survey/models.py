from django.db import models
from django.utils import timezone
from q_accounts.models import User
from q_queues.models import QueueEntry, ServiceType

class SurveyResponse(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    queue_entry = models.ForeignKey(QueueEntry, on_delete=models.CASCADE)
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE)
    rating = models.IntegerField()
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user} - {self.rating}"
