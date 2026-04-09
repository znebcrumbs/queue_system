"""
Role-Based Access Control (RBAC) decorators and utilities.

All access control is permission-based (no hardcoded roles).
Roles are dynamically created CustomRole instances with assigned permissions.
"""

from functools import wraps
import logging
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)


def require_permission(permission_slug):
    """
    Decorator to enforce permission-based access control.
    Checks if user (via their role) has the permission.
    
    Usage:
        @require_permission('manage_users')
        def user_management(request):
            pass
    """
    def decorator(func):
        @wraps(func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not request.user.has_permission(permission_slug):
                # Log denied access attempts
                logger.warning(
                    f"Permission denied for user {request.user.username}: "
                    f"missing '{permission_slug}' permission"
                )
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'error': 'Access denied',
                        'detail': f'Permission required: {permission_slug}'
                    }, status=403)
                return HttpResponseForbidden(f"Permission denied: {permission_slug}")
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(*permission_slugs):
    """
    Decorator to enforce user has ANY of the specified permissions.
    
    Usage:
        @require_any_permission('export_data', 'export_reports')
        def export_view(request):
            pass
    """
    def decorator(func):
        @wraps(func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not request.user.has_any_permission(*permission_slugs):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'error': 'Access denied',
                        'detail': f'One of these permissions required: {", ".join(permission_slugs)}'
                    }, status=403)
                return HttpResponseForbidden(f"Permission denied. Required one of: {', '.join(permission_slugs)}")
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_all_permissions(*permission_slugs):
    """
    Decorator to enforce user has ALL of the specified permissions.
    
    Usage:
        @require_all_permissions('view_reports', 'export_data')
        def advanced_export(request):
            pass
    """
    def decorator(func):
        @wraps(func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not request.user.has_all_permissions(*permission_slugs):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'error': 'Access denied',
                        'detail': f'All of these permissions required: {", ".join(permission_slugs)}'
                    }, status=403)
                return HttpResponseForbidden(f"Permission denied. Required all of: {', '.join(permission_slugs)}")
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def audit_log_action(action_enum):
    """
    Decorator to automatically log view access to audit trail.
    
    Args:
        action_enum: AuditLog.Action enum value
    
    Usage:
        from apps.audit.models import AuditLog
        @audit_log_action(AuditLog.Action.LOGIN)
        def admin_dashboard(request):
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            from apps.audit.models import AuditLog
            
            # Log the access
            if request.user.is_authenticated:
                AuditLog.log(
                    action=action_enum,
                    user=request.user,
                    object_type='View',
                    object_id=0,
                    object_name=func.__name__,
                    description=f"Accessed {func.__name__}",
                    request=request
                )
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator
