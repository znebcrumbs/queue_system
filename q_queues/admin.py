from django.contrib import admin
from .models import ServiceType, QueueEntry

admin.site.register(ServiceType)
admin.site.register(QueueEntry)
