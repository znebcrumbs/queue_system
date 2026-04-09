#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.accounts.models import User, CustomRole

# Find users without custom_role
users_without_role = User.objects.filter(custom_role__isnull=True)
print(f"Users without custom_role:")
for user in users_without_role:
    print(f"  - ID: {user.id}, Username: {user.username}, Email: {user.email}, Is Superuser: {user.is_superuser}")

# Get the admin role
admin_role = CustomRole.objects.get(slug='admin')

# Assign admin role to all users without a role
if users_without_role.count() > 0:
    print(f"\nAssigning admin role to {users_without_role.count()} user(s)...")
    for user in users_without_role:
        user.custom_role = admin_role
        user.save()
        print(f"  ✓ Assigned admin role to {user.username}")
else:
    print("All users already assigned a role!")
