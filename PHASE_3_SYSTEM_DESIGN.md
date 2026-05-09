# PHASE 3 — CORE SYSTEM DESIGN (ARCHITECTURE UPGRADE)

> ⏱️ Estimated time: **2-3 days**
> 
> This phase introduces enterprise-grade features: multi-tenancy via Organizations, Ticket abstraction, RBAC enforcement, and audit logging.

---

## 🏗️ Architecture Overview

Before PHASE 3, the system has:
- ✅ Users with roles (ADMIN, REGISTRAR, MIS)
- ✅ Departments organizing workflows
- ✅ QueueEntry as the main entity

After PHASE 3, the system will have:
- ✅ Organization - Multi-tenant backbone
- ✅ Ticket - Universal ticket abstraction (replaces QueueEntry)
- ✅ AuditLog - Complete audit trail
- ✅ RBAC - Strict role-based access control
- ✅ Dashboard permissions - Role-specific views

```
Organization
├── Users (with role)
├── Departments
│   ├── ServiceTypes
│   └── Tickets
└── AuditLog (tracks all changes)
```

---

## STEP 1 - CREATE ORGANIZATION MODEL

### File: `apps/queues/models.py`

Add this model at the TOP of the file (after imports):

```python
from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from apps.accounts.models import User

class Organization(models.Model):
    """
    Multi-tenant organization container.
    All departments, queues, and tickets belong to an organization.
    """
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    
    # Contact info
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Organizations"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


# MIGRATION: Update existing models to link to Organization
# After creating this model, add this field to:
#
# class User(AbstractUser):
#     organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True)
#
# class Department(models.Model):
#     organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
#
# class QueueEntry(models.Model):
#     organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True)
```

---

## STEP 2 - CREATE TICKET MODEL

### File: `apps/queues/models.py` (add after Organization)

```python
class Ticket(models.Model):
    """
    Universal ticket abstraction layer.
    Replaces QueueEntry with more flexible ticket system.
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
    
    # Unique ticket identifier
    ticket_number = models.CharField(max_length=50, unique=True, db_index=True)
    
    # Organization & Department
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    department = models.ForeignKey('Department', on_delete=models.CASCADE)
    
    # Service & Type
    service_type = models.ForeignKey('ServiceType', on_delete=models.CASCADE)
    ticket_type = models.CharField(max_length=20, choices=Type.choices, default=Type.SERVICE_REQUEST)
    
    # Status & Priority
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.NORMAL)
    
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
    customer_id = models.CharField(max_length=50, blank=True)  # ID/Account number
    
    # QR Code
    qr_code = models.TextField(help_text="UUID-based QR data")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Notes
    notes = models.TextField(blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Performance metrics
    wait_time_minutes = models.IntegerField(null=True, blank=True)  # Auto-calculated
    resolution_time_minutes = models.IntegerField(null=True, blank=True)  # Auto-calculated
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'created_at']),
            models.Index(fields=['department', 'status', 'created_at']),
            models.Index(fields=['assigned_to', 'status']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-generate ticket number if not set
        if not self.ticket_number:
            from django.utils import timezone
            today = timezone.now().date()
            count = Ticket.objects.filter(
                created_at__date=today,
                department=self.department
            ).count() + 1
            prefix = self.service_type.prefix or self.service_type.name[:2].upper()
            self.ticket_number = f"{prefix}-{count:03d}"
        
        # Calculate wait time if started
        if self.started_at and not self.wait_time_minutes:
            delta = (self.started_at - self.created_at).total_seconds() / 60
            self.wait_time_minutes = int(delta)
        
        # Calculate resolution time if completed
        if self.completed_at and not self.resolution_time_minutes:
            delta = (self.completed_at - self.created_at).total_seconds() / 60
            self.resolution_time_minutes = int(delta)
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.ticket_number} - {self.customer_name}"
    
    def mark_in_progress(self, user=None):
        """Mark ticket as in progress."""
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
```

---

## STEP 3 - CREATE AUDIT LOG MODEL

### File: `apps/audit/models.py` (NEW FILE)

```python
from django.db import models
from django.contrib.postgres.fields import JSONField  # or use models.JSONField for Django 3.1+
from django.contrib.auth import get_user_model
from apps.queues.models import Organization

User = get_user_model()

class AuditLog(models.Model):
    """
    Comprehensive audit trail for all important actions.
    Tracks who did what, when, and what changed.
    """
    
    class Action(models.TextChoices):
        # Authentication
        LOGIN = "LOGIN", "User Login"
        LOGOUT = "LOGOUT", "User Logout"
        PASSWORD_CHANGED = "PASSWORD_CHANGED", "Password Changed"
        
        # Ticket Operations
        TICKET_CREATED = "TICKET_CREATED", "Ticket Created"
        TICKET_UPDATED = "TICKET_UPDATED", "Ticket Updated"
        TICKET_COMPLETED = "TICKET_COMPLETED", "Ticket Completed"
        TICKET_CANCELLED = "TICKET_CANCELLED", "Ticket Cancelled"
        TICKET_ASSIGNED = "TICKET_ASSIGNED", "Ticket Assigned"
        
        # Configuration
        DEPARTMENT_CREATED = "DEPT_CREATED", "Department Created"
        DEPARTMENT_UPDATED = "DEPT_UPDATED", "Department Updated"
        SERVICETYPE_CREATED = "SERVICE_CREATED", "Service Type Created"
        SERVICETYPE_UPDATED = "SERVICE_UPDATED", "Service Type Updated"
        
        # User Management
        USER_CREATED = "USER_CREATED", "User Created"
        USER_UPDATED = "USER_UPDATED", "User Updated"
        USER_DELETED = "USER_DELETED", "User Deleted"
        ROLE_CHANGED = "ROLE_CHANGED", "User Role Changed"
        
        # Security
        UNAUTHORIZED_ACCESS = "UNAUTHORIZED", "Unauthorized Access Attempt"
        API_KEY_USED = "API_KEY_USED", "API Key Used"
        
        # System
        SETTINGS_CHANGED = "SETTINGS_CHANGED", "Settings Changed"
        BACKUP_CREATED = "BACKUP_CREATED", "Backup Created"
    
    # Core fields
    action = models.CharField(max_length=50, choices=Action.choices)
    
    # Who did it
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    
    # What changed
    object_type = models.CharField(max_length=100)  # 'Ticket', 'User', 'Department', etc.
    object_id = models.IntegerField()
    object_name = models.CharField(max_length=255, blank=True)  # Display name (e.g., ticket number)
    
    # Before & After
    old_values = models.JSONField(default=dict, blank=True)  # {field: old_value}
    new_values = models.JSONField(default=dict, blank=True)  # {field: new_value}
    
    # Request details
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    
    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    description = models.TextField(blank=True)  # Human-readable description
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['organization', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['object_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.action} - {self.user} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    
    @classmethod
    def log(cls, action, organization, user, object_type, object_id, 
            object_name='', old_values=None, new_values=None, 
            ip_address='0.0.0.0', user_agent='', request=None):
        """
        Convenience method to create audit log entry.
        
        Usage:
            AuditLog.log(
                action=AuditLog.Action.TICKET_CREATED,
                organization=org,
                user=request.user,
                object_type='Ticket',
                object_id=ticket.id,
                object_name=ticket.ticket_number,
                new_values={'status': 'PENDING', 'customer': 'John Doe'},
                request=request
            )
        """
        if request:
            ip_address = cls._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            request_path = request.path[:500]
        
        return cls.objects.create(
            action=action,
            organization=organization,
            user=user,
            object_type=object_type,
            object_id=object_id,
            object_name=object_name,
            old_values=old_values or {},
            new_values=new_values or {},
            ip_address=ip_address,
            user_agent=user_agent,
            request_path=request_path,
        )
    
    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
```

---

## STEP 4 - CREATE AUDIT APP

### Commands:

```powershell
# Create audit app
python manage.py startapp audit apps/audit

# Update settings
# Add 'apps.audit' to INSTALLED_APPS
```

### File: `apps/audit/__init__.py`

```python
# Audit app initialization - will register signals here
default_app_config = 'apps.audit.apps.AuditConfig'
```

### File: `apps/audit/apps.py`

```python
from django.apps import AppConfig

class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.audit'
    
    def ready(self):
        # Import signals when app is ready
        import apps.audit.signals
```

### File: `apps/audit/signals.py`

```python
from django.db.models.signals import post_save, post_delete
from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from apps.queues.models import Ticket, Department, ServiceType
from .models import AuditLog

User = get_user_model()

@receiver(post_save, sender=Ticket)
def log_ticket_change(sender, instance, created, **kwargs):
    """Log ticket creation or updates."""
    if created:
        AuditLog.log(
            action=AuditLog.Action.TICKET_CREATED,
            organization=instance.organization,
            user=instance.created_by,
            object_type='Ticket',
            object_id=instance.id,
            object_name=instance.ticket_number,
            new_values={
                'ticket_number': instance.ticket_number,
                'customer': instance.customer_name,
                'status': instance.status,
            }
        )

@receiver(post_save, sender=User)
def log_user_change(sender, instance, created, **kwargs):
    """Log user creation or updates."""
    if created:
        AuditLog.log(
            action=AuditLog.Action.USER_CREATED,
            organization=instance.organization,
            user=None,
            object_type='User',
            object_id=instance.id,
            object_name=instance.get_full_name() or instance.username,
            new_values={
                'username': instance.username,
                'email': instance.email,
                'role': instance.role,
            }
        )

# Add more signals as needed for other operations
```

---

## STEP 5 - IMPLEMENT RBAC (ROLE-BASED ACCESS CONTROL)

### File: `apps/accounts/decorators.py` (NEW FILE)

```python
from functools import wraps
from django.http import HttpForbidden
from django.shortcuts import redirect

def require_role(*allowed_roles):
    """
    Decorator to restrict view access by user role.
    
    Usage:
        @require_role('ADMIN', 'REGISTRAR')
        def my_view(request):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if not hasattr(request.user, 'role'):
                return HttpForbidden("User has no role assigned")
            
            if request.user.role not in allowed_roles:
                return HttpForbidden(f"You don't have permission to access this resource. Required roles: {', '.join(allowed_roles)}")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_permission(permission_check):
    """
    Decorator for custom permission logic.
    
    Usage:
        def can_edit_ticket(user, ticket):
            return user.role == 'ADMIN' or ticket.assigned_to == user
        
        @require_permission(can_edit_ticket)
        def edit_ticket(request, ticket_id):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if not permission_check(request.user):
                return HttpForbidden("Permission denied")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

### File: `apps/accounts/permissions.py` (NEW FILE)

```python
"""
Permission and RBAC utilities.
"""

class RolePermissions:
    """Define permissions per role."""
    
    PERMISSIONS = {
        'ADMIN': {
            'view_dashboard': True,
            'manage_users': True,
            'manage_departments': True,
            'manage_servicetypes': True,
            'view_all_tickets': True,
            'edit_any_ticket': True,
            'view_reports': True,
            'export_data': True,
            'view_audit_logs': True,
            'manage_settings': True,
        },
        'REGISTRAR': {
            'view_dashboard': True,
            'manage_users': False,
            'manage_departments': False,
            'manage_servicetypes': False,
            'view_all_tickets': False,  # Only own department
            'edit_any_ticket': False,   # Only own tickets
            'view_reports': True,
            'export_data': False,
            'view_audit_logs': False,
            'manage_settings': False,
        },
        'MIS': {
            'view_dashboard': True,
            'manage_users': False,
            'manage_departments': False,
            'manage_servicetypes': False,
            'view_all_tickets': True,  # Read-only
            'edit_any_ticket': False,
            'view_reports': True,
            'export_data': True,
            'view_audit_logs': True,
            'manage_settings': False,
        },
    }
    
    @classmethod
    def has_permission(cls, user_role, permission):
        """Check if role has permission."""
        return cls.PERMISSIONS.get(user_role, {}).get(permission, False)
    
    @classmethod
    def can_view_ticket(cls, user, ticket):
        """Check if user can view a specific ticket."""
        if user.role == 'ADMIN':
            return user.organization == ticket.organization
        elif user.role == 'REGISTRAR':
            return ticket.department == user.department
        elif user.role == 'MIS':
            return user.organization == ticket.organization
        return False
    
    @classmethod
    def can_edit_ticket(cls, user, ticket):
        """Check if user can edit a ticket."""
        if user.role == 'ADMIN':
            return user.organization == ticket.organization
        elif user.role == 'REGISTRAR':
            return ticket.department == user.department
        return False
    
    @classmethod
    def can_assign_ticket(cls, user):
        """Check if user can assign tickets."""
        return user.role in ['ADMIN', 'REGISTRAR']
```

---

## STEP 6 - UPDATE VIEWS WITH RBAC

### File: `apps/queues/views.py`

Add this at the top of the dashboard view:

```python
from apps.accounts.decorators import require_role
from apps.accounts.permissions import RolePermissions

@login_required
@require_role('ADMIN', 'REGISTRAR', 'MIS')
def dashboard(request):
    """Dashboard with role-based filtering."""
    user = request.user
    
    if user.role == 'ADMIN':
        # Admin sees all tickets
        tickets = Ticket.objects.filter(
            organization=user.organization
        ).order_by('-created_at')
    
    elif user.role == 'REGISTRAR':
        # Registrar sees only their department's tickets
        tickets = Ticket.objects.filter(
            department=user.department
        ).order_by('-created_at')
    
    elif user.role == 'MIS':
        # MIS sees all tickets but read-only
        tickets = Ticket.objects.filter(
            organization=user.organization
        ).order_by('-created_at')
    
    context = {
        'tickets': tickets,
        'permissions': RolePermissions.PERMISSIONS.get(user.role, {}),
    }
    return render(request, 'dashboard.html', context)
```

---

## STEP 7 - MIGRATION STRATEGY

### Commands:

```powershell
# Create migrations for new models
python manage.py makemigrations

# Apply migrations (test)
python manage.py migrate --settings=config.settings.dev

# For production: test on staging first
python manage.py migrate --settings=config.settings.prod --dry-run

# Create data migration to copy QueueEntry → Ticket
python manage.py makemigrations --empty apps.queues --name migrate_queueentry_to_ticket
```

### Data Migration Template: `apps/queues/migrations/XXXX_migrate_queueentry_to_ticket.py`

```python
from django.db import migrations
import uuid

def copy_queue_to_ticket(apps, schema_editor):
    """Copy existing QueueEntry data to new Ticket model."""
    QueueEntry = apps.get_model('queues', 'QueueEntry')
    Ticket = apps.get_model('queues', 'Ticket')
    Organization = apps.get_model('queues', 'Organization')
    
    # Get or create default organization
    org, _ = Organization.objects.get_or_create(
        slug='default',
        defaults={'name': 'Default Organization'}
    )
    
    for entry in QueueEntry.objects.all():
        Ticket.objects.create(
            ticket_number=entry.queue_number,
            organization=org,
            department=entry.department,
            service_type=entry.service_type,
            status=entry.status,
            customer_name=entry.name,
            customer_phone=entry.mobile_number,
            customer_email=entry.email,
            qr_code=entry.qr_code_data,
            created_at=entry.created_at,
            completed_at=entry.served_at,
        )

def reverse_copy(apps, schema_editor):
    """Reverse the migration if needed."""
    Ticket = apps.get_model('queues', 'Ticket')
    Ticket.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('queues', '0006_ticket'),  # Adjust based on your migrations
    ]

    operations = [
        migrations.RunPython(copy_queue_to_ticket, reverse_copy),
    ]
```

---

## 📋 Implementation Checklist

- [ ] Create `Organization` model
- [ ] Update `User`, `Department`, `QueueEntry` to link to Organization
- [ ] Create `Ticket` model as primary entity
- [ ] Create `apps/audit` app
- [ ] Create `AuditLog` model with signals
- [ ] Create RBAC decorators and permissions
- [ ] Update views to use @require_role decorator
- [ ] Create and run migrations
- [ ] Test with different user roles
- [ ] Verify audit logs are recording
- [ ] Update admin to show Organization relationships
- [ ] Test data migration (QueueEntry → Ticket)

---

## 🎯 Production Readiness Checklist (After PHASE 3)

- [ ] All users assigned to Organization
- [ ] All departments linked to Organization
- [ ] All tickets have proper organization assignment
- [ ] Audit logs capturing all changes
- [ ] RBAC enforced in all views
- [ ] Dashboard shows correct data per role
- [ ] Kiosk API still works with API key
- [ ] Test with multiple organizations (if using multi-tenancy)

---

## ✅ PHASE 3 Complete Once:

1. ✅ Organization model created and deployed
2. ✅ Ticket model operational with audit trail
3. ✅ RBAC decorators enforcing permissions
4. ✅ Views updated with role checks
5. ✅ Audit signals logging all changes
6. ✅ Tests passing with new models
7. ✅ Data successfully migrated from QueueEntry to Ticket

