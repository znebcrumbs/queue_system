"""
Signals for automatic audit logging of model changes.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from apps.queues.models import Ticket, QueueEntry, Department, ServiceType
from .models import AuditLog

User = get_user_model()


@receiver(post_save, sender=Ticket)
def log_ticket_change(sender, instance, created, update_fields=None, **kwargs):
    """Log ticket creation or updates."""
    if created:
        AuditLog.log(
            action=AuditLog.Action.TICKET_CREATED,
            user=instance.created_by,
            object_type='Ticket',
            object_id=instance.id,
            object_name=instance.ticket_number,
            new_values={
                'ticket_number': instance.ticket_number,
                'customer': instance.customer_name,
                'status': instance.status,
                'priority': instance.priority,
                'type': instance.ticket_type,
            },
            description=f"Ticket {instance.ticket_number} created for {instance.customer_name}"
        )
    else:
        # Log updates
        AuditLog.log(
            action=AuditLog.Action.TICKET_UPDATED,
            user=None,  # Would need to track user from middleware for updates
            object_type='Ticket',
            object_id=instance.id,
            object_name=instance.ticket_number,
            new_values={'status': instance.status},
        )


@receiver(post_save, sender=QueueEntry)
def log_queue_entry_change(sender, instance, created, **kwargs):
    """Log QueueEntry creation or status changes."""
    if created:
        AuditLog.log(
            action=AuditLog.Action.QUEUE_ENTRY_CREATED,
            user=None,
            object_type='QueueEntry',
            object_id=instance.id,
            object_name=instance.queue_number,
            new_values={
                'queue_number': instance.queue_number,
                'customer': instance.name,
                'status': instance.status,
            },
            description=f"Queue entry {instance.queue_number} created"
        )


@receiver(post_save, sender=User)
def log_user_change(sender, instance, created, **kwargs):
    """Log user creation or updates."""
    if created:
        role_name = instance.custom_role.name if instance.custom_role else "No Role"
        AuditLog.log(
            action=AuditLog.Action.USER_CREATED,
            user=None,
            object_type='User',
            object_id=instance.id,
            object_name=instance.get_full_name() or instance.username,
            new_values={
                'username': instance.username,
                'email': instance.email,
                'role': role_name,
                'is_staff': instance.is_staff,
            },
            description=f"User {instance.username} created with role {role_name}"
        )


@receiver(post_save, sender=Department)
def log_department_change(sender, instance, created, **kwargs):
    """Log department creation or updates."""
    if created:
        AuditLog.log(
            action=AuditLog.Action.DEPARTMENT_CREATED,
            user=None,
            object_type='Department',
            object_id=instance.id,
            object_name=instance.name,
            new_values={'name': instance.name, 'slug': instance.slug},
        )


@receiver(post_save, sender=ServiceType)
def log_servicetype_change(sender, instance, created, **kwargs):
    """Log service type creation or updates."""
    if created:
        AuditLog.log(
            action=AuditLog.Action.SERVICETYPE_CREATED,
            user=None,
            object_type='ServiceType',
            object_id=instance.id,
            object_name=instance.name,
            new_values={'name': instance.name, 'prefix': instance.prefix},
        )
