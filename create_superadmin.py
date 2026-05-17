#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.accounts.models import User, CustomRole

# Create superadmin user
if not User.objects.filter(username='superadmin').exists():
    user = User.objects.create_user(
        username='superadmin',
        password='superadmin123',
        is_staff=True,
        is_superuser=True
    )
    # Assign Administrator role
    role = CustomRole.objects.get(name='Administrator')
    user.custom_role = role
    user.save()
    print('✅ Superadmin created')
    print('   Username: superadmin')
    print('   Password: superadmin123')
    print('   Role: Administrator')
    print('   Access: All queues, all departments')
else:
    user = User.objects.get(username='superadmin')
    print('✅ Superadmin already exists')
    print('   Username: superadmin')
    print('   Role: ' + (user.custom_role.name if user.custom_role else 'None'))
