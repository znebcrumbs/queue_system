#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.contrib.auth.models import User
from apps.accounts.models import CustomUser
from apps.queues.models import Department

# Create a test user if it doesn't exist
if not User.objects.filter(username='testuser').exists():
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        is_staff=True
    )
    # Create CustomUser profile
    try:
        dept = Department.objects.first()  # Get first department
        custom_user = CustomUser.objects.create(
            user=user,
            department=dept
        )
        print(f"Created user: {user.username} with CustomUser profile")
    except Exception as e:
        print(f"User created but error creating profile: {e}")
else:
    print("User testuser already exists")
