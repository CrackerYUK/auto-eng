"""Smoke tests for project documentation and FAQ page."""

from pathlib import Path

from django.test import SimpleTestCase, TestCase
from django.urls import reverse


class FaqPageTests(TestCase):
    def test_faq_page_is_public_and_renders(self):
        response = self.client.get(reverse("faq"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "FAQ / Помощь")
        self.assertContains(response, "Что такое система нарядов-допусков")

    def test_base_menu_contains_faq_link(self):
        response = self.client.get(reverse("faq"))

        self.assertContains(response, f'href="{reverse("faq")}"')
        self.assertContains(response, "FAQ")


class DocumentationSmokeTests(SimpleTestCase):
    def read_doc(self, name):
        return Path(name).read_text(encoding="utf-8")

    def test_docx_mapping_uses_translit_variables(self):
        text = self.read_doc("DOCX_TEMPLATE_MAPPING.md")

        self.assertIn("{{ nomer_naryada }}", text)
        self.assertIn("{{ uchastniki_rabot }}", text)
        self.assertIn("Не используйте кириллицу внутри {{ ... }}", text)

    def test_readme_contains_run_and_docx_instructions(self):
        text = self.read_doc("README.md")

        self.assertIn("python manage.py migrate", text)
        self.assertIn("python manage.py runserver", text)
        self.assertIn("DOCX-шаблон", text)
        self.assertIn("FAQ", text)

    def test_project_state_has_required_sections(self):
        text = self.read_doc("PROJECT_STATE.md").lower()

        self.assertIn("реализовано", text)
        self.assertIn("pending", text)
        self.assertIn("известные ограничения", text)
