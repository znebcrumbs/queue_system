from django.db import models, transaction, IntegrityError
import re
from django.utils import timezone
from apps.accounts.models import User

class ServiceType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    prefix = models.CharField(max_length=5, blank=True, null=True)
    department = models.ForeignKey("Department", on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

    def get_prefix(self):
        return (self.prefix or self.name[:2]).upper()

    def generate_queue_number(self):
        today = timezone.now().date()
        count_today = QueueEntry.objects.filter(
        service_type=self, created_at__date=today
                ).count()
    # Use 4-digit format with higher limit (10000 instead of 256)
        number = (count_today % 10000) + 1
        return f"{self.get_prefix()}-{number:04d}"

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
        indexes = [
            models.Index(fields=['created_at', 'status'], name='idx_created_status'),
            models.Index(fields=['department', 'status'], name='idx_dept_status'),
            models.Index(fields=['service_type', 'created_at'], name='idx_service_created'),
            models.Index(fields=['department', 'created_at', 'status'], name='idx_dept_created_status'),
            models.Index(fields=['created_date'], name='idx_created_date'),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.queue_number} - {self.service_type.name}"


# ============================================
# TICKET MODEL - Universal Ticket Abstraction
# ============================================

class Ticket(models.Model):
    """
    Universal ticket model for on-premise queue system.
    Extends QueueEntry with additional metadata and performance tracking.
    """
    
    class Type(models.TextChoices):
        SERVICE_REQUEST = "SERVICE", "Service Request"
        COMPLAINT = "COMPLAINT", "Customer Complaint"
        INQUIRY = "INQUIRY", "General Inquiry"
        FEEDBACK = "FEEDBACK", "Feedback/Survey"
        OTHER = "OTHER", "Other"
    
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        WAITING = "WAITING", "Waiting"
        COMPLETED = "COMPLETED", "Completed/Served"
        CANCELLED = "CANCELLED", "Cancelled"
        RETURNED = "RETURNED", "Returned to Queue"
    
    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        NORMAL = "NORMAL", "Normal"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"
    
    # Core Ticket Info
    ticket_number = models.CharField(max_length=50, unique=True, db_index=True)
    ticket_type = models.CharField(max_length=20, choices=Type.choices, default=Type.SERVICE_REQUEST)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.NORMAL)
    
    # Department & Service
    department = models.ForeignKey(Department, on_delete=models.CASCADE, db_index=True)
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE)
    
    # Assignment
    assigned_to = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_tickets'
    )
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_tickets'
    )
    
    # Customer Information
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_email = models.EmailField(blank=True)
    customer_id = models.CharField(max_length=50, blank=True, help_text="ID or Account number")
    
    # QR Code
    qr_code = models.TextField(help_text="UUID-based unique identifier")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Notes
    notes = models.TextField(blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Performance Metrics
    wait_time_minutes = models.IntegerField(null=True, blank=True)
    resolution_time_minutes = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['department', 'created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['assigned_to', 'status']),
        ]
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
    
    def save(self, *args, **kwargs):
        """Auto-generate ticket number with retry on unique constraint failures and calculate metrics."""
        def _compute_metrics():
            if self.started_at and not self.wait_time_minutes:
                delta = (self.started_at - self.created_at).total_seconds() / 60
                self.wait_time_minutes = int(delta)
            if self.completed_at and not self.resolution_time_minutes:
                delta = (self.completed_at - self.created_at).total_seconds() / 60
                self.resolution_time_minutes = int(delta)

        if not self.ticket_number:
            prefix = (self.service_type.prefix or self.service_type.name[:2]).upper()
            attempt = 0
            while True:
                attempt += 1
                today = timezone.now().date()
                last_ticket = Ticket.objects.filter(
                    created_at__date=today,
                    department=self.department
                ).order_by('-created_at').first()
                if last_ticket and last_ticket.ticket_number:
                    m = re.search(r'-(\d+)$', last_ticket.ticket_number)
                    next_num = int(m.group(1)) + 1 if m else Ticket.objects.filter(created_at__date=today, department=self.department).count() + 1
                else:
                    next_num = 1

                self.ticket_number = f"{prefix}-{next_num:04d}"
                _compute_metrics()

                try:
                    with transaction.atomic():
                        super(Ticket, self).save(*args, **kwargs)
                    break
                except IntegrityError:
                    # Another process may have created the same ticket_number; retry a few times
                    if attempt >= 5:
                        raise
                    # clear ticket_number and try again
                    self.ticket_number = None
                    continue
        else:
            _compute_metrics()
            super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.ticket_number} - {self.customer_name}"
    
    def mark_in_progress(self, user=None):
        """Transition ticket to in-progress."""
        self.status = self.Status.IN_PROGRESS
        self.assigned_to = user
        self.started_at = timezone.now()
        self.save()
    
    def mark_completed(self):
        """Mark ticket as completed."""
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save()
    
    def mark_cancelled(self):
        """Mark ticket as cancelled."""
        self.status = self.Status.CANCELLED
        self.save()

