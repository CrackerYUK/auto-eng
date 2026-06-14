"""Tests for DocumentTemplate admin upload validation."""

from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from docx import Document

from documents.forms import DOCX_TEMPLATE_ERROR_MESSAGE, DocumentTemplateAdminForm
from documents.models import DocumentTemplate


class DocumentTemplateAdminFormTests(TestCase):
    """Checks that broken DOCX templates are rejected before saving."""

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.temp_dir.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(self.temp_dir.cleanup)
        self.user = get_user_model().objects.create_user(username="template-admin")

    def test_valid_docx_template_can_be_saved(self):
        form = self._form(self._docx_upload("valid.docx", "Permit {{ nomer_naryada }}"))

        self.assertTrue(form.is_valid(), form.errors)
        template = form.save()

        self.assertEqual(DocumentTemplate.objects.count(), 1)
        self.assertEqual(template.name, "Validated template")
        self.assertTrue(template.is_active)

    def test_docx_template_with_jinja_syntax_error_is_not_saved(self):
        form = self._form(self._docx_upload("broken.docx", "Permit {{ } }"))

        self.assertFalse(form.is_valid())
        self.assertEqual(DocumentTemplate.objects.count(), 0)
        self.assertIn(DOCX_TEMPLATE_ERROR_MESSAGE, form.errors["file"])

    def test_non_docx_file_is_rejected(self):
        upload = SimpleUploadedFile("template.txt", "{{ nomer_naryada }}".encode("utf-8"), content_type="text/plain")
        form = self._form(upload)

        self.assertFalse(form.is_valid())
        self.assertEqual(DocumentTemplate.objects.count(), 0)
        self.assertIn("Файл шаблона должен быть в формате .docx.", form.errors["file"])

    def test_template_error_message_is_clear_for_user(self):
        form = self._form(self._docx_upload("broken.docx", "Permit {{ } }"))

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["file"], [DOCX_TEMPLATE_ERROR_MESSAGE])

    def _form(self, upload):
        return DocumentTemplateAdminForm(
            data={
                "name": "Validated template",
                "document_type": "permit",
                "version": "validated-1",
                "is_active": "on",
                "uploaded_by": str(self.user.pk),
            },
            files={"file": upload},
        )

    def _docx_upload(self, name, paragraph_text):
        document = Document()
        document.add_paragraph(paragraph_text)
        output = BytesIO()
        document.save(output)
        return SimpleUploadedFile(
            name,
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
