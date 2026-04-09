from django.contrib.auth.models import AbstractUser
from django.db import models
from .permissions import RolePermissions


class CustomPermission(models.Model):
    """
    Predefined permissions that can be assigned to custom roles.
    Operators can create their own permissions as needed.
    """
    CATEGORY_CHOICES = [
        ('dashboard', 'Dashboard & Analytics'),
        ('tickets', 'Ticket Management'),
        ('queues', 'Queue Management'),
        ('users', 'User Management'),
        ('system', 'System Configuration'),
        ('audit', 'Audit & Security'),
        ('exports', 'Data Export & Import'),
        ('custom', 'Custom Permission'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='custom')
    created_at = models.DateTimeField(auto_now_add=True)
    is_builtin = models.BooleanField(default=False)  # Mark built-in permissions
    
    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Custom Permission'
        verbose_name_plural = 'Custom Permissions'
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
    
    @classmethod
    def ensure_builtin_permissions(cls):
        """
        Create default permissions if they don't exist.
        
        Permission Naming Convention:
        =============================
        All permission slugs follow the pattern: action_resource
        
        Examples:
        - create_ticket  (action: create, resource: ticket)
        - view_tickets   (action: view, resource: tickets for listing)
        - manage_user    (action: manage, resource: user for CRUD operations)
        - export_report  (action: export, resource: report)
        
        Rules:
        1. Use lowercase with underscores
        2. Use singular form for resources (ticket, user, report)
        3. Use the exact action verb (create, view, edit, delete, manage, export, import)
        4. For list/view operations: use "view_<resource>s" (view_tickets, view_audit_logs)
        5. For management operations: use "manage_<resource>" (manage_user, manage_department)
        
        DON'T use:
        - camelCase (canViewQueue, manageQueue)
        - Mixed singular/plural ✗ (manage_user, edit_users)
        - Prefix patterns ✗ (permission_view_ticket)
        
        Built-in Permissions (30 total):
        """
        permissions_data = [
            # Dashboard
            ('view_dashboard', 'View Dashboard', 'dashboard', 'Access main dashboard'),
            ('view_analytics', 'View Analytics', 'dashboard', 'View system analytics and metrics'),
            ('view_reports', 'View Reports', 'dashboard', 'View system reports'),
            
            # Tickets
            ('create_ticket', 'Create Ticket', 'tickets', 'Create new tickets'),
            ('view_tickets', 'View Tickets', 'tickets', 'View ticket information'),
            ('edit_tickets', 'Edit Tickets', 'tickets', 'Modify ticket details'),
            ('delete_tickets', 'Delete Tickets', 'tickets', 'Delete tickets'),
            ('complete_tickets', 'Complete Tickets', 'tickets', 'Mark tickets as completed'),
            ('assign_tickets', 'Assign Tickets', 'tickets', 'Assign tickets to staff'),
            ('return_tickets', 'Return Tickets', 'tickets', 'Return tickets to queue'),
            
            # Queues
            ('manage_queues', 'Manage Queues', 'queues', 'Manage queue operations'),
            ('manage_departments', 'Manage Departments', 'queues', 'Configure departments'),
            ('manage_service_types', 'Manage Service Types', 'queues', 'Configure service types'),
            
            # Users
            ('manage_users', 'Manage Users', 'users', 'Create and manage user accounts'),
            ('create_users', 'Create Users', 'users', 'Create new user accounts'),
            ('edit_users', 'Edit Users', 'users', 'Modify user details'),
            ('delete_users', 'Delete Users', 'users', 'Delete user accounts'),
            ('change_roles', 'Change User Roles', 'users', 'Assign roles to users'),
            ('reset_passwords', 'Reset Passwords', 'users', 'Reset user passwords'),
            
            # System
            ('configure_system', 'Configure System', 'system', 'Configure system settings'),
            ('manage_settings', 'Manage Settings', 'system', 'Manage application settings'),
            ('manage_roles', 'Manage Roles', 'system', 'Create and manage roles'),
            ('manage_permissions', 'Manage Permissions', 'system', 'Define permissions'),
            
            # Audit
            ('view_audit_logs', 'View Audit Logs', 'audit', 'View system audit logs'),
            ('export_audit_logs', 'Export Audit Logs', 'audit', 'Export audit logs'),
            ('view_security_events', 'View Security Events', 'audit', 'View security events'),
            
            # Exports
            ('export_data', 'Export Data', 'exports', 'Export system data'),
            ('export_tickets', 'Export Tickets', 'exports', 'Export ticket information'),
            ('export_reports', 'Export Reports', 'exports', 'Export reports'),
            ('import_data', 'Import Data', 'exports', 'Import external data'),
        ]
        
        for slug, name, category, description in permissions_data:
            cls.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'category': category,
                    'description': description,
                    'is_builtin': True,
                }
            )


class CustomRole(models.Model):
    """
    Dynamic role system allowing operators to create custom roles
    with granular permission control.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(CustomPermission, related_name='roles', blank=True)
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_roles')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_system = models.BooleanField(default=False)  # Built-in roles (ADMIN, REGISTRAR, MIS)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Custom Role'
        verbose_name_plural = 'Custom Roles'
    
    def __str__(self):
        return self.name
    
    def has_permission(self, permission_slug):
        """Check if this role has a specific permission."""
        return self.permissions.filter(slug=permission_slug).exists()
    
    @classmethod
    def create_system_roles(cls):
        """Create default system roles if they don't exist."""
        from django.contrib.auth.models import User as DjangoUser
        
        # Get or create system roles
        admin_role, _ = cls.objects.get_or_create(
            slug='admin',
            defaults={
                'name': 'Administrator',
                'description': 'Full system access',
                'is_system': True,
            }
        )
        
        registrar_role, _ = cls.objects.get_or_create(
            slug='registrar',
            defaults={
                'name': 'Registrar',
                'description': 'Create and manage own tickets',
                'is_system': True,
            }
        )
        
        mis_role, _ = cls.objects.get_or_create(
            slug='mis',
            defaults={
                'name': 'Management Information Systems',
                'description': 'Queue operations and reporting',
                'is_system': True,
            }
        )
        
        # Assign permissions to system roles
        admin_perms = CustomPermission.objects.filter(is_builtin=True)
        admin_role.permissions.set(admin_perms)
        
        registrar_perms = CustomPermission.objects.filter(
            slug__in=['view_dashboard', 'create_ticket', 'view_tickets', 'edit_tickets']
        )
        registrar_role.permissions.set(registrar_perms)
        
        mis_perms = CustomPermission.objects.filter(
            slug__in=[
                'view_dashboard', 'view_analytics', 'view_reports',
                'view_tickets', 'complete_tickets', 'assign_tickets',
                'manage_queues', 'view_audit_logs', 'export_data'
            ]
        )
        mis_role.permissions.set(mis_perms)


class User(AbstractUser):
    """
    Custom user model with unified role system via ForeignKey to CustomRole.
    All permissions are managed through the role's permission set (no hardcoded roles).
    """
    
    department = models.ForeignKey(
        "queues.Department", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="User's primary department for department-level permission filtering"
    )
    custom_role = models.ForeignKey(
        CustomRole, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='users',
        help_text="User's assigned role which determines permissions"
    )

    def __str__(self):
        role_name = self.custom_role.name if self.custom_role else "No Role"
        return f"{self.username} ({role_name})"
    
    def has_permission(self, permission_slug):
        """
        Check if user has a specific permission via their role.
        
        Uses caching to avoid repeated DB queries:
        - First call queries the DB
        - Subsequent calls use cached permission set
        - Superusers always have all permissions (prevents lockout)
        
        Usage:
            if request.user.has_permission('manage_users'):
                # do admin stuff
        """
        # Superuser override: always has all permissions
        if self.is_superuser:
            return True
        
        if not self.custom_role:
            return False
        
        # Cache permissions on the user instance
        if not hasattr(self, '_perm_cache'):
            self._perm_cache = set(
                self.custom_role.permissions.values_list('slug', flat=True)
            )
        
        return permission_slug in self._perm_cache
    
    def has_any_permission(self, *permission_slugs):
        """Check if user has any of the specified permissions (uses cache)."""
        for perm in permission_slugs:
            if self.has_permission(perm):
                return True
        return False
    
    def has_all_permissions(self, *permission_slugs):
        """Check if user has all of the specified permissions (uses cache)."""
        for perm in permission_slugs:
            if not self.has_permission(perm):
                return False
        return True
    
    def get_all_permissions(self):
        """Get set of all permission slugs for this user (uses cache)."""
        if not self.custom_role:
            return set()
        
        if not hasattr(self, '_perm_cache'):
            self._perm_cache = set(
                self.custom_role.permissions.values_list('slug', flat=True)
            )
        
        return self._perm_cache
    
    def can_manage_department(self, department_id):
        """
        Check if user can manage a specific department.
        
        Rules:
        - If user has 'configure_system' or 'manage_departments' permission → can manage any
        - Otherwise → can only manage own department
        """
        if self.has_any_permission('configure_system', 'manage_departments'):
            return True
        
        # User can only manage their own department
        if self.department_id == department_id:
            return True
        
        return False
    
    def can_view_department(self, department_id):
        """
        Check if user can view a specific department's data.
        
        Rules:
        - If 'view_analytics' permission → can view all departments
        - Otherwise → can only view own department
        """
        if self.has_permission('view_analytics'):
            return True
        
        # User can only view their own department
        if self.department_id == department_id:
            return True
        
        return False
    
    def clear_permission_cache(self):
        """
        Clear cached permissions (call after role change).
        Used when a user's role is modified.
        """
        if hasattr(self, '_perm_cache'):
            delattr(self, '_perm_cache')


