from django.contrib import admin
from .models import ServiceType, QueueEntry

@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(QueueEntry)
class QueueEntryAdmin(admin.ModelAdmin):
    list_display = ("queue_number", "service_type", "client", "status", "created_at", "served_at")
    list_filter = ("status", "service_type", "created_at")
    search_fields = ("queue_number", "client__username")
    ordering = ("created_at",)
