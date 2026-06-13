"""Admin registrations for the audit app."""

from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "object_type", "object_id", "user", "created_at")
    list_filter = ("action", "object_type", "created_at")
    search_fields = ("action", "object_type", "object_id", "user__username")
    readonly_fields = ("created_at",)
