from django.db import models
from django.utils import timezone
from apps.accounts.models import User  
  

class ServiceType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    prefix = models.CharField(max_length=5, blank=True, null=True)
    department = models.ForeignKey("Department", on_delete=models.CASCADE, null=True, blank=True)

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
                ).count()
    # roll over every 256 tickets
        number = (count_today % 256) + 1
        return f"{self.get_prefix()}-{number:01d}"

#prio class

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=100, unique=True)    
    # Maximum queue entries that this department will accept per day.
    # A value of 0 means no limit.
    max_entries_per_day = models.PositiveIntegerField(default=0, help_text="Maximum tickets per day (0 = unlimited)")

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            # Generate a slug from the name field
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


    def __str__(self):
        return self.name


class QueueEntry(models.Model):
    class Status(models.TextChoices):
        WAITING = "WAITING", "Waiting"
        SERVED = "SERVED", "Served"
        RETURNED = "RETURNED", "Returned"
        CANCELLED = "CANCELLED", "Cancelled"

    client = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    service_type = models.ForeignKey("ServiceType", on_delete=models.CASCADE)
    queue_number = models.CharField(max_length=10)  # NO unique=True
    qr_code_data = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.WAITING)
    created_at = models.DateTimeField(default=timezone.now)
    served_at = models.DateTimeField(null=True, blank=True)
    created_date = models.DateField(auto_now_add=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=50)   
    email = models.EmailField(max_length=254)         
    section = models.CharField(max_length=100)        

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["queue_number", "service_type", "created_at"],
                name="unique_queue_per_service_per_day"
            )
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.queue_number} - {self.service_type.name}"

