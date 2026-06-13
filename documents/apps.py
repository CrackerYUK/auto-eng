"""Django application configuration for documents."""

from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    """Configuration for the documents app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "documents"
