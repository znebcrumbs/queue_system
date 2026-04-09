from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, CustomRole, CustomPermission


@admin.register(CustomPermission)
class CustomPermissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'category', 'is_builtin', 'created_at')
    list_filter = ('category', 'is_builtin', 'created_at')
    search_fields = ('name', 'slug', 'description')
    readonly_fields = ('is_builtin', 'created_at')
    fieldsets = (
        ('Permission Info', {
            'fields': ('name', 'slug', 'description', 'category')
        }),
        ('Status', {
            'fields': ('is_builtin', 'created_at')
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deleting built-in permissions
        if obj and obj.is_builtin:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(CustomRole)
class CustomRoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'permission_count', 'is_system', 'is_active', 'created_at')
    list_filter = ('is_system', 'is_active', 'created_at')
    search_fields = ('name', 'slug', 'description')
    filter_horizontal = ('permissions',)
    readonly_fields = ('is_system', 'created_by', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Role Info', {
            'fields': ('name', 'slug', 'description', 'is_active')
        }),
        ('Permissions', {
            'fields': ('permissions',),
            'description': 'Select permissions this role will have'
        }),
        ('System', {
            'fields': ('is_system', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def permission_count(self, obj):
        return obj.permissions.count()
    permission_count.short_description = 'Permissions'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new role
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deleting system roles
        if obj and obj.is_system:
            return False
        return super().has_delete_permission(request, obj)
    
    def has_change_permission(self, request, obj=None):
        # System roles can only be changed by superuser
        if obj and obj.is_system and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Permissions", {"fields": ("custom_role", "department")}),
    )
    list_display = ("username", "email", "custom_role", "department", "is_staff", "is_superuser")
    list_filter = ("custom_role", "is_staff", "is_superuser", "department")
    search_fields = ("username", "email")
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        # Show custom_role field only if role is set to CUSTOM
        return fieldsets


admin.site.site_header = "Queue Management System Admin"
admin.site.site_title = "QMS Admin Portal"
admin.site.index_title = "Welcome to the Queue System Admin"

