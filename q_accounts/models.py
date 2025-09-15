from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrator"
        REGISTRAR = "REGISTRAR", "REGISTRAR"
        MIS = "MIS", "MIS"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MIS
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
