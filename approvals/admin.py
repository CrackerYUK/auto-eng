"""Admin registrations for the approvals app."""

from django.contrib import admin

from .models import ApprovalAction


@admin.register(ApprovalAction)
class ApprovalActionAdmin(admin.ModelAdmin):
    list_display = ("permit", "actor", "action", "old_status", "new_status", "created_at")
    list_filter = ("action", "old_status", "new_status", "created_at")
    search_fields = ("permit__number", "actor__username", "comment")
    readonly_fields = ("created_at",)
