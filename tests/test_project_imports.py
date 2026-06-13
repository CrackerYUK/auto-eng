"""Smoke tests for the initial Django project scaffold."""

from django.apps import apps
from django.conf import settings
from django.test import SimpleTestCase


REQUIRED_LOCAL_APPS = {"users", "permits", "approvals", "documents", "audit"}


class ProjectScaffoldTests(SimpleTestCase):
    """Checks that work with Django's built-in test runner and pytest."""

    def test_settings_module_imports(self):
        """The Django settings module should be importable and configured."""
        self.assertEqual(settings.ROOT_URLCONF, "permit_system.urls")

    def test_required_local_apps_are_installed(self):
        """All baseline permit-system apps should be present in INSTALLED_APPS."""
        self.assertTrue(REQUIRED_LOCAL_APPS.issubset(set(settings.INSTALLED_APPS)))

    def test_required_local_apps_are_registered(self):
        """Django app registry should contain all baseline apps."""
        registered_app_labels = {app_config.label for app_config in apps.get_app_configs()}
        self.assertTrue(REQUIRED_LOCAL_APPS.issubset(registered_app_labels))
