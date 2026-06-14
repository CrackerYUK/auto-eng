"""Document generation services."""

from io import BytesIO
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from docxtpl import DocxTemplate

from documents.models import DocumentTemplate, GeneratedDocument
from permits.models import Permit


class PdfConversionError(RuntimeError):
    """Raised when DOCX to PDF conversion cannot be completed safely."""


DOCX_TEMPLATE_ERROR_MESSAGE = "Ошибка в DOCX-шаблоне. Проверьте фигурные скобки и переменные."


def generate_template_demo_docx(template_id):
    """Render a DOCX template with safe demo data without creating GeneratedDocument."""
    template = DocumentTemplate.objects.get(pk=template_id)
    try:
        docx_template = DocxTemplate(template.file.path)
        docx_template.render(_build_demo_template_context(template))
        output = BytesIO()
        docx_template.save(output)
        output.seek(0)
    except Exception as exc:
        raise ValidationError(DOCX_TEMPLATE_ERROR_MESSAGE) from exc
    return output.getvalue(), _demo_docx_name(template)


@transaction.atomic
def generate_permit_docx(permit_id, template_id, user):
    """Generate and store a DOCX document for a permit from a DOCX template."""
    permit = (
        Permit.objects.select_related(
            "responsible_manager",
            "work_supervisor",
            "created_by",
            "work_area",
            "equipment",
            "work_type",
        )
        .prefetch_related("hazards", "safety_measures")
        .get(pk=permit_id)
    )
    template = DocumentTemplate.objects.get(pk=template_id)

    docx_template = DocxTemplate(template.file.path)
    docx_template.render(_build_permit_context(permit, template))

    output = BytesIO()
    docx_template.save(output)
    output.seek(0)

    generated_document = GeneratedDocument(
        permit=permit,
        template=template,
        generated_by=user,
    )
    generated_document.file_docx.save(
        _generated_docx_name(permit, template),
        ContentFile(output.getvalue()),
        save=False,
    )
    generated_document.save()
    return generated_document


def convert_docx_to_pdf(generated_document_id):
    """Convert a generated DOCX to PDF when PDF conversion is explicitly enabled."""
    if not settings.PDF_CONVERTER_ENABLED:
        raise PdfConversionError("PDF conversion is disabled. Set PDF_CONVERTER_ENABLED=1 to enable it.")

    soffice_path = shutil.which(settings.SOFFICE_PATH)
    if not soffice_path:
        raise PdfConversionError(
            "LibreOffice/soffice executable was not found. Set SOFFICE_PATH to enable PDF conversion."
        )

    generated_document = GeneratedDocument.objects.get(pk=generated_document_id)
    if not generated_document.file_docx:
        raise PdfConversionError("Generated DOCX file is missing; PDF conversion cannot be started.")

    docx_path = Path(generated_document.file_docx.path)
    if not docx_path.exists():
        raise PdfConversionError(f"Generated DOCX file does not exist: {docx_path}")

    with TemporaryDirectory() as output_dir:
        output_path = Path(output_dir) / f"{docx_path.stem}.pdf"
        command = [
            soffice_path,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            output_dir,
            str(docx_path),
        ]
        try:
            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            raise PdfConversionError(
                f"PDF conversion failed: {exc.stderr or exc.stdout or exc}"
            ) from exc

        if not output_path.exists():
            raise PdfConversionError("PDF conversion finished but no PDF file was produced.")

        generated_document.file_pdf.save(
            _generated_pdf_name(generated_document),
            ContentFile(output_path.read_bytes()),
            save=True,
        )
    return generated_document


def _build_permit_context(permit, template=None):
    hazard_names = [hazard.name for hazard in permit.hazards.all()]
    safety_measure_names = [measure.name for measure in permit.safety_measures.all()]
    equipment_name = permit.equipment.name if permit.equipment else ""
    equipment_code = permit.equipment.code if permit.equipment else ""
    responsible_manager_name = _user_display_name(permit.responsible_manager)
    work_supervisor_name = _user_display_name(permit.work_supervisor)
    responsible_manager_text = permit.responsible_manager_text or ""
    work_producer_text = permit.work_producer_text or ""
    responsible_manager_result = responsible_manager_text or responsible_manager_name
    work_producer_result = work_producer_text or work_supervisor_name
    created_by_name = _user_display_name(permit.created_by)
    template_name = template.name if template else ""
    template_version = template.version if template else ""

    return {
        "permit": {
            "id": permit.pk,
            "number": permit.number,
            "status": permit.status,
            "status_display": permit.get_status_display(),
            "created_at": permit.created_at,
            "work_starts_at": permit.work_starts_at,
            "work_ends_at": permit.work_ends_at,
            "work_location": permit.work_location or "",
            "responsible_manager_text": responsible_manager_text,
            "work_producer_text": work_producer_text,
            "work_nature_text": permit.work_nature_text or "",
            "additional_conditions": permit.additional_conditions or "",
            "additional_safety_notes": permit.additional_safety_notes or "",
            "work_area": permit.work_area,
            "work_area_name": permit.work_area.name,
            "equipment": permit.equipment,
            "equipment_name": equipment_name,
            "equipment_code": equipment_code,
            "work_type": permit.work_type,
            "work_type_name": permit.work_type.name,
            "hazards": list(permit.hazards.all()),
            "hazard_names": hazard_names,
            "hazard_names_text": ", ".join(hazard_names),
            "safety_measures": list(permit.safety_measures.all()),
            "safety_measure_names": safety_measure_names,
            "safety_measure_names_text": ", ".join(safety_measure_names),
            "work_description": permit.work_description or "",
            "responsible_manager": permit.responsible_manager,
            "responsible_manager_name": responsible_manager_name,
            "work_supervisor": permit.work_supervisor,
            "work_supervisor_name": work_supervisor_name,
            "created_by": permit.created_by,
            "created_by_name": created_by_name,
            "updated_at": permit.updated_at,
        },
        "номер_наряда": permit.number or "",
        "статус_наряда": permit.get_status_display() or "",
        "участок": permit.work_area.name if permit.work_area else "",
        "оборудование": equipment_name,
        "вид_работ": permit.work_type.name if permit.work_type else "",
        "место_работ": permit.work_location or "",
        "описание_работ": permit.work_description or "",
        "характер_работ": permit.work_nature_text or "",
        "дополнительные_условия": permit.additional_conditions or "",
        "дополнительные_меры_безопасности": permit.additional_safety_notes or "",
        "дата_начала": _format_docx_date(permit.work_starts_at),
        "дата_окончания": _format_docx_date(permit.work_ends_at),
        "дата_создания": _format_docx_date(permit.created_at),
        "ответственный_руководитель": responsible_manager_result,
        "производитель_работ": work_producer_result,
        "создал_пользователь": created_by_name,
        "опасности": ", ".join(hazard_names),
        "меры_безопасности": ", ".join(safety_measure_names),
        "шаблон_документа": template_name,
        "версия_шаблона": template_version,
    }


def _build_demo_template_context(template):
    """Build representative DOCX context for checking templates without a real Permit."""
    demo_date = timezone.localtime(timezone.now()).strftime("%d.%m.%Y")
    template_name = template.name if template else ""
    template_version = template.version if template else ""
    hazard_text = "Высота, Электрическое напряжение"
    safety_text = "Ограждение зоны работ, Проверка СИЗ"
    return {
        "permit": {
            "id": "demo",
            "number": "DEMO-001",
            "status": "draft",
            "status_display": "Draft",
            "created_at": demo_date,
            "work_starts_at": demo_date,
            "work_ends_at": demo_date,
            "work_location": "Площадка обслуживания насосной станции",
            "responsible_manager_text": "Иванов Иван Иванович",
            "work_producer_text": "Петров Пётр Петрович",
            "work_nature_text": "Осмотр и ремонт запорной арматуры",
            "additional_conditions": "Работы выполнять после инструктажа и допуска ответственного лица.",
            "additional_safety_notes": "Использовать каски, очки и диэлектрические перчатки.",
            "work_area_name": "Цех 1",
            "equipment_name": "Насос H-101",
            "equipment_code": "H-101",
            "work_type_name": "Ремонтные работы",
            "hazard_names": hazard_text.split(", "),
            "hazard_names_text": hazard_text,
            "safety_measure_names": safety_text.split(", "),
            "safety_measure_names_text": safety_text,
            "work_description": "Демонстрационная проверка DOCX-шаблона.",
            "responsible_manager_name": "Иванов Иван Иванович",
            "work_supervisor_name": "Петров Пётр Петрович",
            "created_by_name": "operator",
            "updated_at": demo_date,
        },
        "номер_наряда": "DEMO-001",
        "статус_наряда": "Draft",
        "участок": "Цех 1",
        "оборудование": "Насос H-101",
        "вид_работ": "Ремонтные работы",
        "место_работ": "Площадка обслуживания насосной станции",
        "описание_работ": "Демонстрационная проверка DOCX-шаблона.",
        "характер_работ": "Осмотр и ремонт запорной арматуры",
        "дополнительные_условия": "Работы выполнять после инструктажа и допуска ответственного лица.",
        "дополнительные_меры_безопасности": "Использовать каски, очки и диэлектрические перчатки.",
        "дата_начала": demo_date,
        "дата_окончания": demo_date,
        "дата_создания": demo_date,
        "ответственный_руководитель": "Иванов Иван Иванович",
        "производитель_работ": "Петров Пётр Петрович",
        "создал_пользователь": "operator",
        "опасности": hazard_text,
        "меры_безопасности": safety_text,
        "шаблон_документа": template_name,
        "версия_шаблона": template_version,
    }


def _format_docx_date(value):
    if not value:
        return ""
    return timezone.localtime(value).strftime("%d.%m.%Y")


def _user_display_name(user):
    if not user:
        return ""
    full_name = user.get_full_name().strip()
    return full_name or user.get_username() or ""


def _demo_docx_name(template):
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    return f"template_{template.pk}_demo_{timestamp}.docx"


def _generated_docx_name(permit, template):
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    return f"permit_{permit.number}_template_{template.pk}_{timestamp}.docx"


def _generated_pdf_name(generated_document):
    docx_name = Path(generated_document.file_docx.name).stem
    return f"{docx_name}.pdf"
