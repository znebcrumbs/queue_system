from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AuditLog(models.Model):
    """
    Comprehensive audit trail for on-premise queue system.
    Tracks who did what, when, and what changed.
    """
    
    class Action(models.TextChoices):
        # Authentication
        LOGIN = "LOGIN", "User Login"
        LOGOUT = "LOGOUT", "User Logout"
        PASSWORD_CHANGED = "PASSWORD_CHANGED", "Password Changed"
        FAILED_LOGIN = "FAILED_LOGIN", "Failed Login Attempt"
        
        # Ticket Operations
        TICKET_CREATED = "TICKET_CREATED", "Ticket Created"
        TICKET_UPDATED = "TICKET_UPDATED", "Ticket Updated"
        TICKET_COMPLETED = "TICKET_COMPLETED", "Ticket Completed"
        TICKET_CANCELLED = "TICKET_CANCELLED", "Ticket Cancelled"
        TICKET_ASSIGNED = "TICKET_ASSIGNED", "Ticket Assigned"
        TICKET_RETURNED = "TICKET_RETURNED", "Ticket Returned"
        
        # Queue Operations
        QUEUE_ENTRY_CREATED = "QUEUE_ENTRY_CREATED", "Queue Entry Created"
        QUEUE_ENTRY_UPDATED = "QUEUE_ENTRY_UPDATED", "Queue Entry Updated"
        QUEUE_ENTRY_SERVED = "QUEUE_ENTRY_SERVED", "Queue Entry Served"
        
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
        API_KEY_USED = "API_KEY_USED", "Kiosk API Key Used"
        PERMISSION_DENIED = "PERMISSION_DENIED", "Permission Denied"
        
        # System
        SETTINGS_CHANGED = "SETTINGS_CHANGED", "Settings Changed"
        EXPORT_CREATED = "EXPORT_CREATED", "Data Export Created"
    
    # What happened
    action = models.CharField(max_length=50, choices=Action.choices, db_index=True)
    description = models.TextField(blank=True)
    
    # Who did it
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    
    # What changed
    object_type = models.CharField(max_length=100, db_index=True)  # 'Ticket', 'QueueEntry', 'User', etc.
    object_id = models.IntegerField()
    object_name = models.CharField(max_length=255, blank=True)  # Display name
    
    # Before & After
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    
    # Request details
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    http_method = models.CharField(max_length=10, blank=True)  # GET, POST, PUT, DELETE, etc.
    
    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'action']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['object_type', 'object_id']),
            models.Index(fields=['action']),
        ]
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
    
    def __str__(self):
        return f"{self.action} - {self.object_name or self.object_type}:{self.object_id}"
    
    @classmethod
    def log(cls, action, user, object_type, object_id, object_name='',
            old_values=None, new_values=None, description='', request=None):
        """
        Convenience method to create audit log entry.
        
        Usage:
            AuditLog.log(
                action=AuditLog.Action.TICKET_CREATED,
                user=request.user,
                object_type='Ticket',
                object_id=ticket.id,
                object_name=ticket.ticket_number,
                new_values={'status': 'PENDING'},
                request=request
            )
        """
        ip_address = None
        user_agent = ''
        request_path = ''
        http_method = ''
        
        if request:
            ip_address = cls._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            request_path = request.path[:500]
            http_method = request.method
        
        return cls.objects.create(
            action=action,
            user=user if (user and user.is_authenticated) else None,
            object_type=object_type,
            object_id=object_id,
            object_name=object_name,
            old_values=old_values or {},
            new_values=new_values or {},
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            request_path=request_path,
            http_method=http_method,
        )
    
    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request, handling proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
