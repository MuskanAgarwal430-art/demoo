from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import AdminUser, AuditLog, DeviceLog


@admin.register(AdminUser)
class AdminUserAdmin(UserAdmin):
    list_display = ["email", "name", "role", "company", "is_active"]
    list_filter = ["role", "is_active", "company"]
    search_fields = ["email", "name"]
    ordering = ["email"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("name", "phone", "avatar")}),
        ("Company", {"fields": ("company", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "name", "password1", "password2", "role", "company")}),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["action", "resource_type", "resource_id", "admin_user", "created_at"]
    list_filter = ["action", "resource_type"]
    readonly_fields = ["created_at"]


@admin.register(DeviceLog)
class DeviceLogAdmin(admin.ModelAdmin):
    list_display = ["admin_user", "event_type", "device_model", "created_at"]
    list_filter = ["event_type"]
