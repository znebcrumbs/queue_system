from django.contrib import admin
from django.utils.html import format_html
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for audit logs."""
    
    list_display = ('timestamp', 'action_badge', 'user', 'object_display', 'http_method_badge', 'ip_address')
    list_filter = ('action', 'timestamp', 'http_method', 'object_type')
    search_fields = ('user__username', 'object_name', 'description', 'ip_address')
    readonly_fields = (
        'action', 'user', 'object_type', 'object_id', 'object_name',
        'old_values', 'new_values', 'ip_address', 'user_agent', 
        'request_path', 'http_method', 'timestamp', 'description'
    )
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    fieldsets = (
        ('Action Info', {
            'fields': ('timestamp', 'action', 'description', 'http_method')
        }),
        ('User', {
            'fields': ('user', 'ip_address', 'user_agent')
        }),
        ('Object Changed', {
            'fields': ('object_type', 'object_id', 'object_name')
        }),
        ('Changes', {
            'fields': ('old_values', 'new_values')
        }),
        ('Request', {
            'fields': ('request_path',),
            'classes': ('collapse',)
        }),
    )
    
    def action_badge(self, obj):
        """Color-coded action badge."""
        color_map = {
            'LOGIN': '#28a745',  # Green
            'LOGOUT': '#6c757d',  # Gray
            'UNAUTHORIZED': '#dc3545',  # Red
            'PERMISSION_DENIED': '#fd7e14',  # Orange
        }
        color = color_map.get(obj.action, '#0066cc')  # Blue default
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_action_display()
        )
    action_badge.short_description = 'Action'
    
    def object_display(self, obj):
        """Display object with type."""
        return f"{obj.object_type}: {obj.object_name or obj.object_id}"
    object_display.short_description = 'Object'
    
    def http_method_badge(self, obj):
        """Color-coded HTTP method."""
        colors = {
            'GET': '#0066cc',
            'POST': '#28a745',
            'PUT': '#fd7e14',
            'DELETE': '#dc3545',
        }
        color = colors.get(obj.http_method, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.http_method or 'N/A'
        )
    http_method_badge.short_description = 'Method'
    
    def has_add_permission(self, request):
        """Audit logs should not be manually created."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Audit logs should not be deleted."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Audit logs are read-only."""
        return False
