from django.apps import AppConfig


class QAccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    label = 'accounts'
    
    def ready(self):
        """
        Auto-bootstrap RBAC system on app startup.
        Ensures all system roles and permissions always exist.
        """
        try:
            from apps.accounts.models import CustomPermission, CustomRole
            # Ensure all built-in permissions exist
            CustomPermission.ensure_builtin_permissions()
            # Ensure system roles exist
            CustomRole.create_system_roles()
        except Exception as e:
            # Silently fail during migrations or if tables don't exist yet
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"RBAC bootstrap skipped: {e}")



