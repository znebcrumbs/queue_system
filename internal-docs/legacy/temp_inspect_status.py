import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()
from apps.queues.models import QueueEntry
print(dict(QueueEntry.Status.choices))
print('IN_PROGRESS' in dict(QueueEntry.Status.choices))
