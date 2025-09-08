from django.contrib import admin
from .models import QueueEntry, ServiceType


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)

@admin.register(QueueEntry)
class QueueEntryAdmin(admin.ModelAdmin):
    list_display = ("queue_number", "service_type", "status", "client", "created_at", "served_at")
    list_filter = ("status", "service_type", "created_at")
    search_fields = ("queue_number", "service_type__name", "client__username")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "served_at")
