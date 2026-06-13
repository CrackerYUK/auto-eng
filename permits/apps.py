"""Django application configuration for permits."""

from django.apps import AppConfig


class PermitsConfig(AppConfig):
    """Configuration for the permits app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "permits"
