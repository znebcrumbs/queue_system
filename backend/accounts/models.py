from django.db import models
from django.utils import timezone
from accounts.models import User

class ServiceType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class QueueEntry(models.Model):
    class Status(models.TextChoices):
        WAITING = "WAITING", "Waiting"
        SERVED = "SERVED", "Served"
        RETURNED = "RETURNED", "Returned"
        CANCELLED = "CANCELLED", "Cancelled"

    client = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE)
    queue_number = models.CharField(max_length=10)
    qr_code_data = models.TextField()  # Can store encoded URL or token
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING
    )
    created_at = models.DateTimeField(default=timezone.now)
    served_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.queue_number} - {self.status}"
