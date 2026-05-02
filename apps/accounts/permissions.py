"""
Role and Permission definitions for on-premise queue system.
"""

from enum import Enum


class RolePermissions:
    """
    Define what each role can do in the system.
    On-premise deployment: ADMIN, REGISTRAR, MIS
    """
    
    ADMIN = {
        'name': 'Administrator',
        'permissions': {
            
            'view_dashboard': True,
            'view_analytics': True,
            'view_reports': True,
            
           
            'create_ticket': True,
            'view_tickets': True,
            'edit_tickets': True,
            'delete_tickets': True,
            'assign_tickets': True,
            'complete_tickets': True,
            
            
            'manage_queues': True,
            'manage_departments': True,
            'manage_service_types': True,
            
            
            'manage_users': True,
            'create_users': True,
            'edit_users': True,
            'delete_users': True,
            'change_roles': True,
            'reset_passwords': True,
            
            
            'configure_system': True,
            'manage_settings': True,
            
            
            'view_audit_logs': True,
            'export_audit_logs': True,
            'view_security_events': True,
            
            
            'export_data': True,
            'export_tickets': True,
            'export_reports': True,
            'import_data': True,
        }
    }
    
    REGISTRAR = {
        'name': 'Registrar',
        'permissions': {
            # Dashboard
            'view_dashboard': True,
            'view_analytics': False,
            'view_reports': False,
            
            # Ticket Management
            'create_ticket': True,
            'view_tickets': True,
            'edit_tickets': True,  # Only own tickets
            'delete_tickets': False,
            'assign_tickets': False,
            'complete_tickets': False,
            
            # Queue Management
            'manage_queues': False,
            'manage_departments': False,
            'manage_service_types': False,
            
            # User Management
            'manage_users': False,
            'create_users': False,
            'edit_users': False,
            'delete_users': False,
            'change_roles': False,
            'reset_passwords': False,
            
            # System Settings
            'configure_system': False,
            'manage_settings': False,
            
            # Audit & Security
            'view_audit_logs': False,
            'export_audit_logs': False,
            'view_security_events': False,
            
            # Data Export
            'export_data': False,
            'export_tickets': False,
            'export_reports': False,
            'import_data': False,
        }
    }
    
    MIS = {
        'name': 'Management Information Systems',
        'permissions': {
            # Dashboard
            'view_dashboard': True,
            'view_analytics': True,
            'view_reports': True,
            
            # Ticket Management
            'create_ticket': True,
            'view_tickets': True,
            'edit_tickets': True,
            'delete_tickets': False,
            'assign_tickets': True,
            'complete_tickets': True,
            
            # Queue Management
            'manage_queues': True,
            'manage_departments': False,
            'manage_service_types': False,
            
            # User Management
            'manage_users': False,
            'create_users': False,
            'edit_users': False,
            'delete_users': False,
            'change_roles': False,
            'reset_passwords': False,
            
            # System Settings
            'configure_system': False,
            'manage_settings': False,
            
            # Audit & Security
            'view_audit_logs': True,
            'export_audit_logs': False,
            'view_security_events': False,
            
            # Data Export
            'export_data': True,
            'export_tickets': True,
            'export_reports': True,
            'import_data': False,
        }
    }
    
    KIOSK = {
        'name': 'Kiosk (API Only)',
        'permissions': {
            # Minimal permissions for kiosk endpoints
            'create_ticket': True,
            'view_tickets': True,
            'get_queue_status': True,
        }
    }
    
    @classmethod
    def get_role_permissions(cls, role):
        """Get all permissions for a role."""
        role_config = getattr(cls, role, None)
        if role_config:
            return role_config['permissions']
        return {}
    
    @classmethod
    def get_role_name(cls, role):
        """Get display name for a role."""
        role_config = getattr(cls, role, None)
        if role_config:
            return role_config['name']
        return role
    
    @classmethod
    def has_permission(cls, role, permission):
        """Check if role has permission."""
        permissions = cls.get_role_permissions(role)
        return permissions.get(permission, False)
    
    @classmethod
    def all_roles(cls):
        """Get all available roles."""
        return ['ADMIN', 'REGISTRAR', 'MIS', 'KIOSK']
    
    @classmethod
    def role_choices(cls):
        """Get Django choices for role field."""
        return [
            ('ADMIN', cls.get_role_name('ADMIN')),
            ('REGISTRAR', cls.get_role_name('REGISTRAR')),
            ('MIS', cls.get_role_name('MIS')),
            ('KIOSK', cls.get_role_name('KIOSK')),
        ]
