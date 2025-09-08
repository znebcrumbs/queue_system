from django.contrib import admin
from .models import SurveyResponse

@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ("user", "service_type", "queues_entry", "rating", "created_at")
    list_filter = ("rating", "service_type", "created_at")
    search_fields = ("user__username", "feedback")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)