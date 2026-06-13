"""Models for the approvals app."""

from django.conf import settings
from django.db import models

from permits.models import PermitStatus


class ApprovalAction(models.Model):
    """History entry for a status-changing approval action."""

    permit = models.ForeignKey(
        "permits.Permit",
        on_delete=models.CASCADE,
        related_name="approval_actions",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="approval_actions",
    )
    action = models.CharField(max_length=64)
    old_status = models.CharField(max_length=32, choices=PermitStatus.choices)
    new_status = models.CharField(max_length=32, choices=PermitStatus.choices)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.permit} — {self.action}"
