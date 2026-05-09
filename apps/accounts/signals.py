"""
Signal handlers for RBAC system.
Handles cache invalidation when roles or permissions change.
"""

from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)


def clear_user_perm_cache_on_role_permission_change(sender, instance, action, **kwargs):
    """
    Clear user permission caches when role permissions are modified.
    
    Triggered when:
    - Role.permissions.add() called
    - Role.permissions.remove() called
    - Role.permissions.clear() called
    
    Args:
        sender: CustomRole.permissions.through
        instance: CustomRole instance
        action: 'pre_add', 'post_add', 'pre_remove', 'post_remove', 'pre_clear', 'post_clear'
    """
    # Only process after changes are complete
    if action in ['post_add', 'post_remove', 'post_clear']:
        # Get all users with this role
        users_with_role = instance.user_set.all()
        
        count = 0
        for user in users_with_role:
            # Clear the permission cache on user instances
            if hasattr(user, '_perm_cache'):
                delattr(user, '_perm_cache')
                count += 1
        
        if count > 0:
            logger.info(
                f"Cleared permission cache for {count} users "
                f"after role '{instance.name}' permissions changed (action={action})"
            )


def clear_user_perm_cache_on_user_save(sender, instance, created, **kwargs):
    """
    Clear user permission caches when a user's role is changed.
    
    Triggered when User.custom_role is modified and saved.
    """
    if not created:
        # User was updated (not newly created)
        # Clear their cache so next permission check fetches fresh
        if hasattr(instance, '_perm_cache'):
            delattr(instance, '_perm_cache')
            logger.debug(f"Cleared permission cache for user {instance.username}")


def register_signals():
    """Register all RBAC signal handlers."""
    from apps.accounts.models import User, CustomRole
    
    # Connect m2m_changed signal for role permissions
    m2m_changed.connect(
        clear_user_perm_cache_on_role_permission_change,
        sender=CustomRole.permissions.through,
        dispatch_uid='rbac_role_permissions_changed'
    )
    
    # Connect post_save signal for user changes
    post_save.connect(
        clear_user_perm_cache_on_user_save,
        sender=User,
        dispatch_uid='rbac_user_role_changed'
    )
