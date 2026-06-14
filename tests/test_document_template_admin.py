"""Tests for DocumentTemplate admin helper pages."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class DocumentTemplateAdminHelpTests(TestCase):
    """Checks that DOCX template variable help is available in admin."""

    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password",
        )
        self.client.force_login(self.admin_user)

    def test_template_variables_help_page_is_available(self):
        response = self.client.get(reverse("admin:documents_documenttemplate_template_variables"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Переменные DOCX-шаблона")
        self.assertContains(response, "{{ номер_наряда }}")
        self.assertContains(response, "{{ меры_безопасности }}")
        self.assertContains(response, "не ставить пробел между фигурными скобками")

    def test_document_template_changelist_links_to_variable_help(self):
        response = self.client.get(reverse("admin:documents_documenttemplate_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Переменные шаблона")
        self.assertContains(response, reverse("admin:documents_documenttemplate_template_variables"))
