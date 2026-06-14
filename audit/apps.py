"""Django application configuration for audit."""

from django.apps import AppConfig


class AuditConfig(AppConfig):
    """Configuration for the audit app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "audit"
    verbose_name = "Аудит"
