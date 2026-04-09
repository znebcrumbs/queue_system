"""
API Security middleware and utilities.
Handles authentication, authorization, rate limiting, and logging for API endpoints.
"""

import json
import logging
import functools
from django.conf import settings
from django.http import JsonResponse
from apps.audit.models import AuditLog

logger = logging.getLogger(__name__)


class APISecurityMiddleware:
    """
    Middleware for API security: logging requests/responses, tracking access,
    and enforcing security policies on API endpoints.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip for non-API requests
        if not request.path.startswith('/api/'):
            return self.get_response(request)
        
        response = self.get_response(request)
        
        # Log API access
        if request.user.is_authenticated:
            # Log API access to audit trail
            if response.status_code >= 400:
                # Log errors
                action = AuditLog.Action.UNAUTHORIZED_ACCESS
                if response.status_code == 403:
                    action = AuditLog.Action.PERMISSION_DENIED
            else:
                action = AuditLog.Action.API_KEY_USED
            
            AuditLog.log(
                action=action,
                user=request.user,
                object_type='API',
                object_id=0,
                object_name=request.path,
                description=f"{request.method} {request.path} - Status {response.status_code}",
                request=request
            )
        
        return response


def api_authentication_required(view_func):
    """
    Decorator for API endpoints that require valid API key authentication.
    Checks X-API-Key header or api_key query parameter.
    
    Usage:
        @api_authentication_required
        def api_endpoint(request):
            pass
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Get API key from header or query params
        api_key = (
            request.headers.get('X-API-Key') or 
            request.GET.get('api_key') or 
            request.POST.get('api_key')
        )
        
        # Check if API key is valid
        if not api_key or api_key != settings.KIOSK_API_KEY:
            logger.warning(f"API authentication failed: {request.method} {request.path} from {request.META.get('REMOTE_ADDR')}")
            
            # Log to audit trail
            AuditLog.log(
                action=AuditLog.Action.UNAUTHORIZED_ACCESS,
                user=None,
                object_type='API',
                object_id=0,
                object_name=request.path,
                description=f"Invalid API key attempt on {request.path}",
                request=request
            )
            
            return JsonResponse(
                {'error': 'Authentication failed', 'detail': 'Invalid or missing API key'},
                status=401
            )
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def api_rate_limit(max_requests=100, time_window=3600):
    """
    Decorator to implement rate limiting on API endpoints.
    
    Args:
        max_requests: Maximum number of requests allowed
        time_window: Time window in seconds (default 1 hour)
    
    Usage:
        @api_rate_limit(max_requests=50, time_window=3600)
        def api_endpoint(request):
            pass
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            from django.core.cache import cache
            
            # Get identifier (API key or IP address)
            identifier = (
                request.headers.get('X-API-Key') or 
                request.POST.get('api_key') or
                request.META.get('REMOTE_ADDR')
            )
            
            cache_key = f"api_rate_limit_{identifier}"
            current_count = cache.get(cache_key, 0)
            
            if current_count >= max_requests:
                logger.warning(f"Rate limit exceeded for {identifier}")
                AuditLog.log(
                    action=AuditLog.Action.UNAUTHORIZED_ACCESS,
                    user=request.user if request.user.is_authenticated else None,
                    object_type='API',
                    object_id=0,
                    object_name=request.path,
                    description=f"Rate limit exceeded - {current_count} requests in {time_window}s",
                    request=request
                )
                return JsonResponse(
                    {'error': 'Rate limit exceeded', 'detail': f'Maximum {max_requests} requests per {time_window} seconds'},
                    status=429
                )
            
            # Increment counter
            cache.set(cache_key, current_count + 1, time_window)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def api_permission_required(permission_name):
    """
    Decorator to enforce permission-based access control on API endpoints.
    User must have the specified permission.
    
    Usage:
        @api_permission_required('export_data')
        def api_export(request):
            pass
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse(
                    {'error': 'Authentication required'},
                    status=401
                )
            
            if not request.user.has_permission(permission_name):
                logger.warning(f"API permission denied for user {request.user.username}: {permission_name}")
                AuditLog.log(
                    action=AuditLog.Action.PERMISSION_DENIED,
                    user=request.user,
                    object_type='API',
                    object_id=0,
                    object_name=request.path,
                    description=f"Missing permission: {permission_name}",
                    request=request
                )
                return JsonResponse(
                    {'error': 'Permission denied', 'detail': f'Required permission: {permission_name}'},
                    status=403
                )
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def api_permission_required(*permissions):
    """
    Decorator to enforce permission-based access control on API endpoints.
    User must have one of the specified permissions.
    
    Usage:
        @api_permission_required('configure_system', 'manage_queues')
        def api_admin(request):
            pass
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse(
                    {'error': 'Authentication required'},
                    status=401
                )
            
            # Check if user has any of the required permissions
            has_permission = any(
                request.user.has_permission(perm) for perm in permissions
            )
            
            if not has_permission:
                logger.warning(
                    f"API permission denied for user {request.user.username}: "
                    f"has {list(request.user.get_all_permissions())}, required {permissions}"
                )
                AuditLog.log(
                    action=AuditLog.Action.PERMISSION_DENIED,
                    user=request.user,
                    object_type='API',
                    object_id=0,
                    object_name=request.path,
                    description=f"User missing required permissions {permissions}",
                    request=request
                )
                return JsonResponse(
                    {'error': 'Access denied', 'detail': f'Required permissions: {", ".join(permissions)}'},
                    status=403
                )
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


class APIResponseInterceptor:
    """
    Utility class to standardize API responses with consistent JSON structure.
    """
    
    @staticmethod
    def success(data=None, message='Success', status_code=200):
        """Return standardized success response."""
        return JsonResponse({
            'success': True,
            'message': message,
            'data': data,
        }, status=status_code)
    
    @staticmethod
    def error(error, detail='', status_code=400):
        """Return standardized error response."""
        return JsonResponse({
            'success': False,
            'error': error,
            'detail': detail,
        }, status=status_code)
    
    @staticmethod
    def paginated(queryset, page_size=20, page=1):
        """Return paginated response."""
        total = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        items = list(queryset[start:end].values())
        
        return {
            'items': items,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'pages': (total + page_size - 1) // page_size,
            }
        }


class APIAuditLogger:
    """
    Centralized audit logging for API operations.
    """
    
    @staticmethod
    def log_access(action, user, object_type, object_id, request, 
                   object_name='', description='', old_values=None, new_values=None):
        """
        Log API access/modification to audit trail.
        
        Args:
            action: AuditLog.Action choice
            user: User instance or None
            object_type: Type of object (e.g., 'Ticket', 'QueueEntry')
            object_id: ID of the object
            request: HTTP request object
            object_name: Display name of the object
            description: Detailed description of the action
            old_values: Dict of previous values (for updates)
            new_values: Dict of new values
        """
        AuditLog.log(
            action=action,
            user=user,
            object_type=object_type,
            object_id=object_id,
            object_name=object_name,
            old_values=old_values or {},
            new_values=new_values or {},
            description=description,
            request=request
        )
    
    @staticmethod
    def log_error(error_type, user, request, description=''):
        """
        Log API errors (unauthorized, permission denied, etc.)
        
        Args:
            error_type: Type of error (UNAUTHORIZED, PERMISSION_DENIED, etc.)
            user: User instance or None
            request: HTTP request object
            description: Error description
        """
        AuditLog.log(
            action=error_type,
            user=user,
            object_type='API',
            object_id=0,
            object_name=request.path,
            description=description or f"API error on {request.method} {request.path}",
            request=request
        )


def validate_json_payload(required_fields=None):
    """
    Decorator to validate JSON request payload.
    
    Usage:
        @validate_json_payload(['email', 'password'])
        def api_login(request):
            data = json.loads(request.body)
            # data is guaranteed to have 'email' and 'password'
    """
    if required_fields is None:
        required_fields = []
    
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse(
                    {'error': 'Invalid JSON', 'detail': 'Request body must be valid JSON'},
                    status=400
                )
            
            # Check required fields
            missing_fields = [f for f in required_fields if f not in data]
            if missing_fields:
                return JsonResponse(
                    {'error': 'Missing fields', 'detail': f'Required: {", ".join(missing_fields)}'},
                    status=400
                )
            
            # Store parsed data in request for use in view
            request._json_data = data
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator
