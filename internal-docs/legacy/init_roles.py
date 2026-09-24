import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.accounts.models import CustomPermission, CustomRole

CustomPermission.ensure_builtin_permissions()
CustomRole.create_system_roles()

print('✅ Built-in permissions and system roles created')
print(f"✅ {CustomPermission.objects.filter(is_builtin=True).count()} built-in permissions")
print(f"✅ {CustomRole.objects.filter(is_system=True).count()} system roles")
