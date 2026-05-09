from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.audit'
    verbose_name = 'Audit Logs'
    
    def ready(self):
        """Register signals when app is ready."""
        import apps.audit.signals  # noqa
