from django import template

register = template.Library()

@register.filter
def has_permission(user, permission_name):
    """
    Custom template filter to check if a user has a specific permission.
    Usage: {% if user|has_permission:"permission_name" %}
    """
    if not user or not user.is_authenticated:
        return False
    
    # Check if user has the permission using the has_permission method
    if hasattr(user, 'has_permission'):
        return user.has_permission(permission_name)
    
    return False
