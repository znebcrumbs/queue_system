from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Profile", {"fields": ("role", "department")}),
    )
    list_display = ("username", "email", "role", "department", "is_staff", "is_superuser")
    list_filter = ("role", "is_staff", "is_superuser", "department")
    search_fields = ("username", "email")
from django.contrib import admin

admin.site.site_header = "Queue Management System Admin"
admin.site.site_title = "QMS Admin Portal"
admin.site.index_title = "Welcome to the Queue System Admin"
