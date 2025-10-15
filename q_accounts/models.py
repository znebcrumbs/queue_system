from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrator"
        STAFF= "REGISTRAR", "REGISTRAR"
        MIS = "MIS", "MIS"

    department = models.ForeignKey("q_queues.Department", on_delete=models.SET_NULL, null=True, blank=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MIS
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
