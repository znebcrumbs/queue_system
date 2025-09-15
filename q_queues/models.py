from django.db import models
from django.utils import timezone
from q_accounts.models import User

from django.conf import settings
from django.db import models
from django.utils import timezone
from q_accounts.models import User   # ✅ import the real model

class ServiceType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    prefix = models.CharField(max_length=5, blank=True, null=True)

    # Correct: use Role.choices from User
    assigned_role = models.CharField(
        max_length=20,
        choices=User.Role.choices,
        default=User.Role.MIS
    )

    def __str__(self):
        return self.name

    def get_prefix(self):
        return (self.prefix or self.name[:2]).upper()

    def generate_queue_number(self):
        today = timezone.now().date()
        count_today = QueueEntry.objects.filter(
            service_type=self, created_at__date=today
        ).count() + 1
        return f"{self.get_prefix()}-{count_today:01d}"



class QueueEntry(models.Model):
    class Status(models.TextChoices):
        WAITING = "WAITING", "Waiting"
        SERVED = "SERVED", "Served"
        RETURNED = "RETURNED", "Returned"
        CANCELLED = "CANCELLED", "Cancelled"

    client = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE)
    queue_number = models.CharField(max_length=10)
    qr_code_data = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING
    )
    created_at = models.DateTimeField(default=timezone.now)
    served_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.queue_number} - {self.service_type.name}"
