"""Django application configuration for approvals."""

from django.apps import AppConfig


class ApprovalsConfig(AppConfig):
    """Configuration for the approvals app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "approvals"
    verbose_name = "Согласования"
