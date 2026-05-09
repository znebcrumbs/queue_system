#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.accounts.models import User, CustomRole, CustomPermission

# Check if there are users without custom_role
users_without_role = User.objects.filter(custom_role__isnull=True)
print(f"Users without custom_role: {users_without_role.count()}")

# Check existing system roles
system_roles = CustomRole.objects.filter(is_system=True)
print(f"\nSystem roles found: {system_roles.count()}")
for role in system_roles:
    print(f"  - {role.name} (slug: {role.slug})")

# Check permissions
permissions = CustomPermission.objects.all()
print(f"\nTotal permissions: {permissions.count()}")

# Show a few permissions
for perm in permissions[:5]:
    print(f"  - {perm.name} ({perm.slug})")

# If there are users without roles, alert
if users_without_role.count() > 0:
    print(f"\n⚠️ WARNING: {users_without_role.count()} users without custom_role!")
    print("These users will not have any permissions until assigned a role.")
