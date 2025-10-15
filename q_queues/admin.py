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

admin.site.site_header = "Queue Management System Admin"
admin.site.site_title = "QMS Admin Portal"
admin.site.index_title = "Welcome to the Queue System Admin"

from django.contrib import admin
from .models import Department

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)