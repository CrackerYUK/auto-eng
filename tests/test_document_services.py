"""Tests for DOCX document generation services."""

from datetime import timedelta
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from docx import Document

from documents.models import DocumentTemplate, GeneratedDocument
from documents.services import (
    PdfConversionError,
    _build_permit_context,
    convert_docx_to_pdf,
    generate_permit_docx,
)
from permits.models import Equipment, Hazard, Permit, SafetyMeasure, WorkArea, WorkType


class GeneratePermitDocxTests(TestCase):
    """Checks that permit data is rendered into DOCX templates."""

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.temp_dir.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(self.temp_dir.cleanup)

        user_model = get_user_model()
        self.creator = user_model.objects.create_user(username="creator")
        self.manager = user_model.objects.create_user(username="manager")
        self.supervisor = user_model.objects.create_user(username="supervisor")
        self.generator = user_model.objects.create_user(username="generator")
        self.work_area = WorkArea.objects.create(name="Boiler house", description="Main boiler area")
        self.equipment = Equipment.objects.create(
            name="Valve A",
            code="V-100",
            work_area=self.work_area,
            description="Steam valve",
        )
        self.work_type = WorkType.objects.create(name="Repair", description="Repair work")
        self.hazard = Hazard.objects.create(name="Steam", description="Hot steam")
        self.safety_measure = SafetyMeasure.objects.create(name="PPE", description="Wear PPE")

        starts_at = timezone.now() + timedelta(days=1)
        self.permit = Permit.objects.create(
            number="PT-DOCX-001",
            work_starts_at=starts_at,
            work_ends_at=starts_at + timedelta(hours=8),
            work_location="Boiler room",
            work_area=self.work_area,
            equipment=self.equipment,
            work_type=self.work_type,
            work_description="Inspect and repair valve",
            responsible_manager=self.manager,
            work_supervisor=self.supervisor,
            created_by=self.creator,
        )
        self.permit.hazards.add(self.hazard)
        self.permit.safety_measures.add(self.safety_measure)
        self.template = DocumentTemplate.objects.create(
            name="Permit DOCX template",
            document_type="permit",
            version="docx-test-1",
            file=SimpleUploadedFile(
                "permit_template.docx",
                self._template_bytes(),
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
            uploaded_by=self.creator,
        )

    def test_generate_permit_docx_renders_template_and_saves_generated_document(self):
        generated_document = generate_permit_docx(
            permit_id=self.permit.pk,
            template_id=self.template.pk,
            user=self.generator,
        )

        self.assertIsInstance(generated_document, GeneratedDocument)
        self.assertEqual(generated_document.permit, self.permit)
        self.assertEqual(generated_document.template, self.template)
        self.assertEqual(generated_document.generated_by, self.generator)
        self.assertTrue(generated_document.file_docx.name.endswith(".docx"))
        self.assertEqual(generated_document.file_pdf.name, "")

        rendered_doc = Document(generated_document.file_docx.path)
        rendered_text = "\n".join(paragraph.text for paragraph in rendered_doc.paragraphs)
        self.assertIn("Permit PT-DOCX-001", rendered_text)
        self.assertIn("Location Boiler room", rendered_text)
        self.assertIn("Supervisor supervisor", rendered_text)
        self.assertIn("Description Inspect and repair valve", rendered_text)
        self.assertIn("Work area Boiler house", rendered_text)
        self.assertIn("Equipment Valve A V-100", rendered_text)
        self.assertIn("Work type Repair", rendered_text)
        self.assertIn("Hazards Steam", rendered_text)
        self.assertIn("Safety PPE", rendered_text)
        self.assertIn("Номер PT-DOCX-001", rendered_text)
        self.assertIn("Статус Draft", rendered_text)
        self.assertIn("Участок Boiler house", rendered_text)
        self.assertIn("Оборудование Valve A", rendered_text)
        self.assertIn("Вид работ Repair", rendered_text)
        self.assertIn("Место Boiler room", rendered_text)
        self.assertIn("Описание Inspect and repair valve", rendered_text)
        self.assertIn(f"Дата начала {timezone.localtime(self.permit.work_starts_at):%d.%m.%Y}", rendered_text)
        self.assertIn(f"Дата окончания {timezone.localtime(self.permit.work_ends_at):%d.%m.%Y}", rendered_text)
        self.assertIn(f"Дата создания {timezone.localtime(self.permit.created_at):%d.%m.%Y}", rendered_text)
        self.assertIn("Ответственный manager", rendered_text)
        self.assertIn("Производитель supervisor", rendered_text)
        self.assertIn("Создал creator", rendered_text)
        self.assertIn("Опасности Steam", rendered_text)
        self.assertIn("Меры PPE", rendered_text)
        self.assertIn("Шаблон Permit DOCX template", rendered_text)
        self.assertIn("Версия docx-test-1", rendered_text)

    def test_build_permit_context_contains_reference_directory_fields(self):
        context = _build_permit_context(self.permit)["permit"]

        self.assertEqual(context["work_area_name"], "Boiler house")
        self.assertEqual(context["equipment_name"], "Valve A")
        self.assertEqual(context["equipment_code"], "V-100")
        self.assertEqual(context["work_type_name"], "Repair")
        self.assertEqual(context["hazard_names"], ["Steam"])
        self.assertEqual(context["hazard_names_text"], "Steam")
        self.assertEqual(context["safety_measure_names"], ["PPE"])
        self.assertEqual(context["safety_measure_names_text"], "PPE")

    def test_build_permit_context_contains_russian_docx_aliases(self):
        context = _build_permit_context(self.permit, self.template)

        self.assertEqual(context["номер_наряда"], "PT-DOCX-001")
        self.assertEqual(context["статус_наряда"], "Draft")
        self.assertEqual(context["участок"], "Boiler house")
        self.assertEqual(context["оборудование"], "Valve A")
        self.assertEqual(context["вид_работ"], "Repair")
        self.assertEqual(context["место_работ"], "Boiler room")
        self.assertEqual(context["описание_работ"], "Inspect and repair valve")
        self.assertEqual(context["дата_начала"], timezone.localtime(self.permit.work_starts_at).strftime("%d.%m.%Y"))
        self.assertEqual(context["дата_окончания"], timezone.localtime(self.permit.work_ends_at).strftime("%d.%m.%Y"))
        self.assertEqual(context["дата_создания"], timezone.localtime(self.permit.created_at).strftime("%d.%m.%Y"))
        self.assertEqual(context["ответственный_руководитель"], "manager")
        self.assertEqual(context["производитель_работ"], "supervisor")
        self.assertEqual(context["создал_пользователь"], "creator")
        self.assertEqual(context["опасности"], "Steam")
        self.assertEqual(context["меры_безопасности"], "PPE")
        self.assertEqual(context["шаблон_документа"], "Permit DOCX template")
        self.assertEqual(context["версия_шаблона"], "docx-test-1")

    @override_settings(PDF_CONVERTER_ENABLED=False)
    def test_convert_docx_to_pdf_reports_disabled_converter(self):
        generated_document = self._generated_document_with_docx()

        with self.assertRaisesMessage(PdfConversionError, "PDF conversion is disabled"):
            convert_docx_to_pdf(generated_document.pk)

    @override_settings(PDF_CONVERTER_ENABLED=True, SOFFICE_PATH="missing-soffice")
    @patch("documents.services.shutil.which", return_value=None)
    def test_convert_docx_to_pdf_reports_missing_soffice(self, _which):
        generated_document = self._generated_document_with_docx()

        with self.assertRaisesMessage(PdfConversionError, "LibreOffice/soffice executable was not found"):
            convert_docx_to_pdf(generated_document.pk)

    @override_settings(PDF_CONVERTER_ENABLED=True, SOFFICE_PATH="soffice")
    @patch("documents.services.shutil.which", return_value="/usr/bin/soffice")
    @patch("documents.services.subprocess.run")
    def test_convert_docx_to_pdf_saves_pdf_with_mocked_soffice(self, run_mock, _which):
        generated_document = self._generated_document_with_docx()

        def fake_run(command, **_kwargs):
            output_dir = Path(command[command.index("--outdir") + 1])
            docx_path = Path(command[-1])
            output_dir.joinpath(f"{docx_path.stem}.pdf").write_bytes(b"%PDF-1.4 demo")

        run_mock.side_effect = fake_run

        converted_document = convert_docx_to_pdf(generated_document.pk)

        self.assertEqual(converted_document.pk, generated_document.pk)
        self.assertTrue(converted_document.file_pdf.name.endswith(".pdf"))
        with converted_document.file_pdf.open("rb") as pdf_file:
            self.assertEqual(pdf_file.read(), b"%PDF-1.4 demo")
        run_mock.assert_called_once()

    def _template_bytes(self):
        document = Document()
        document.add_paragraph("Permit {{ permit.number }}")
        document.add_paragraph("Location {{ permit.work_location }}")
        document.add_paragraph("Supervisor {{ permit.work_supervisor_name }}")
        document.add_paragraph("Description {{ permit.work_description }}")
        document.add_paragraph("Work area {{ permit.work_area_name }}")
        document.add_paragraph("Equipment {{ permit.equipment_name }} {{ permit.equipment_code }}")
        document.add_paragraph("Work type {{ permit.work_type_name }}")
        document.add_paragraph("Hazards {{ permit.hazard_names_text }}")
        document.add_paragraph("Safety {{ permit.safety_measure_names_text }}")
        document.add_paragraph("Номер {{ номер_наряда }}")
        document.add_paragraph("Статус {{ статус_наряда }}")
        document.add_paragraph("Участок {{ участок }}")
        document.add_paragraph("Оборудование {{ оборудование }}")
        document.add_paragraph("Вид работ {{ вид_работ }}")
        document.add_paragraph("Место {{ место_работ }}")
        document.add_paragraph("Описание {{ описание_работ }}")
        document.add_paragraph("Дата начала {{ дата_начала }}")
        document.add_paragraph("Дата окончания {{ дата_окончания }}")
        document.add_paragraph("Дата создания {{ дата_создания }}")
        document.add_paragraph("Ответственный {{ ответственный_руководитель }}")
        document.add_paragraph("Производитель {{ производитель_работ }}")
        document.add_paragraph("Создал {{ создал_пользователь }}")
        document.add_paragraph("Опасности {{ опасности }}")
        document.add_paragraph("Меры {{ меры_безопасности }}")
        document.add_paragraph("Шаблон {{ шаблон_документа }}")
        document.add_paragraph("Версия {{ версия_шаблона }}")
        output = BytesIO()
        document.save(output)
        return output.getvalue()

    def _generated_document_with_docx(self):
        generated_document = GeneratedDocument.objects.create(
            permit=self.permit,
            template=self.template,
            generated_by=self.generator,
        )
        generated_document.file_docx.save(
            "generated-test.docx",
            ContentFile(b"demo docx"),
            save=True,
        )
        return generated_document
