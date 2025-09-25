from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Role", {"fields": ("role",)}),
    )
    list_display = ("username", "email", "role", "is_staff", "is_superuser")
from django.contrib import admin

admin.site.site_header = "Queue Management System Admin"
admin.site.site_title = "QMS Admin Portal"
admin.site.index_title = "Welcome to the Queue System Admin"
