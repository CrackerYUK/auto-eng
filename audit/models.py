"""Models for the audit app."""

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Audit trail entry for significant user actions."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField("Действие", max_length=128)
    object_type = models.CharField("Тип объекта", max_length=128)
    object_id = models.CharField("ID объекта", max_length=128)
    details = models.JSONField("Детали", default=dict, blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Запись аудита"
        verbose_name_plural = "Журнал аудита"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.action} {self.object_type}:{self.object_id}"
