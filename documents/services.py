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
from permits.models import Permit, PermitParticipantRole


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
        .prefetch_related(
            "hazards",
            "safety_measures",
            "participants__personnel__group",
            "participants__personnel__work_area",
        )
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
    participant_context = _build_participant_context(
        permit,
        responsible_manager_fallback=responsible_manager_result,
        work_producer_fallback=work_producer_result,
    )

    context = {
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
        "nomer_naryada": permit.number or "",
        "status_naryada": permit.get_status_display() or "",
        "uchastok": permit.work_area.name if permit.work_area else "",
        "oborudovanie": equipment_name,
        "vid_rabot": permit.work_type.name if permit.work_type else "",
        "mesto_rabot": permit.work_location or "",
        "opisanie_rabot": permit.work_description or "",
        "harakter_rabot": permit.work_nature_text or "",
        "data_nachala": _format_docx_date(permit.work_starts_at),
        "data_okonchaniya": _format_docx_date(permit.work_ends_at),
        "data_sozdaniya": _format_docx_date(permit.created_at),
        "sozdal_polzovatel": created_by_name,
        "opasnosti": ", ".join(hazard_names),
        "mery_bezopasnosti": ", ".join(safety_measure_names),
        "dopolnitelnye_usloviya": permit.additional_conditions or "",
        "dopolnitelnye_mery_bezopasnosti": permit.additional_safety_notes or "",
        "shablon_dokumenta": template_name,
        "versiya_shablona": template_version,
    }
    context.update(participant_context)
    return context


def _build_participant_context(permit, responsible_manager_fallback="", work_producer_fallback=""):
    participants = permit.participants.select_related(
        "personnel",
        "personnel__group",
        "personnel__work_area",
    )
    grouped = {role: [] for role in PermitParticipantRole.values}
    all_participants = []
    for participant in participants:
        formatted = _format_participant(participant)
        if not formatted:
            continue
        grouped.setdefault(participant.role, []).append(formatted)
        all_participants.append(formatted)

    responsible_managers = grouped.get(PermitParticipantRole.RESPONSIBLE_MANAGER, [])
    work_producers = grouped.get(PermitParticipantRole.WORK_PRODUCER, [])
    responsible_manager = responsible_managers[0] if responsible_managers else responsible_manager_fallback
    work_producer = work_producers[0] if work_producers else work_producer_fallback

    return {
        "otvetstvennye_rukovoditeli": "\n".join(responsible_managers) or responsible_manager_fallback or "",
        "proizvoditeli_rabot": "\n".join(work_producers) or work_producer_fallback or "",
        "ispolniteli": "\n".join(grouped.get(PermitParticipantRole.PERFORMER, [])),
        "chleny_brigady": "\n".join(grouped.get(PermitParticipantRole.BRIGADE_MEMBER, [])),
        "dopuskayushchie": "\n".join(grouped.get(PermitParticipantRole.ADMITTING_PERSON, [])),
        "nablyudayushchie": "\n".join(grouped.get(PermitParticipantRole.OBSERVER, [])),
        "prochie_uchastniki": "\n".join(grouped.get(PermitParticipantRole.OTHER, [])),
        "uchastniki_rabot": "\n".join(all_participants),
        "otvetstvennyy_rukovoditel": responsible_manager or "",
        "proizvoditel_rabot": work_producer or "",
    }


def _format_participant(participant):
    if participant.personnel_id:
        value = participant.personnel.full_name
        if participant.personnel.position:
            value = f"{value} — {participant.personnel.position}"
    else:
        value = participant.manual_name.strip()
    if participant.note:
        value = f"{value} ({participant.note})"
    return value


def _build_demo_template_context(template):
    """Build representative DOCX context for checking templates without a real Permit."""
    demo_date = timezone.localtime(timezone.now()).strftime("%d.%m.%Y")
    template_name = template.name if template else ""
    template_version = template.version if template else ""
    hazard_text = "Высота, Электрическое напряжение"
    safety_text = "Ограждение зоны работ, Проверка СИЗ"
    responsible = "Иванов Иван Иванович — мастер участка"
    producer = "Петров Пётр Петрович — производитель работ"
    performer = "Сидоров Сергей Сергеевич — слесарь"
    brigade_member = "Кузнецов Алексей Викторович — электромонтёр"
    admitting = "Демо допускающий вручную (ручной ввод для проверки шаблона)"
    all_participants = "\n".join([responsible, producer, performer, brigade_member, admitting])
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
            "responsible_manager_text": responsible,
            "work_producer_text": producer,
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
            "responsible_manager_name": responsible,
            "work_supervisor_name": producer,
            "created_by_name": "operator",
            "updated_at": demo_date,
        },
        "nomer_naryada": "DEMO-001",
        "status_naryada": "Draft",
        "uchastok": "Цех 1",
        "oborudovanie": "Насос H-101",
        "vid_rabot": "Ремонтные работы",
        "mesto_rabot": "Площадка обслуживания насосной станции",
        "opisanie_rabot": "Демонстрационная проверка DOCX-шаблона.",
        "harakter_rabot": "Осмотр и ремонт запорной арматуры",
        "data_nachala": demo_date,
        "data_okonchaniya": demo_date,
        "data_sozdaniya": demo_date,
        "otvetstvennyy_rukovoditel": responsible,
        "proizvoditel_rabot": producer,
        "sozdal_polzovatel": "operator",
        "opasnosti": hazard_text,
        "mery_bezopasnosti": safety_text,
        "dopolnitelnye_usloviya": "Работы выполнять после инструктажа и допуска ответственного лица.",
        "dopolnitelnye_mery_bezopasnosti": "Использовать каски, очки и диэлектрические перчатки.",
        "shablon_dokumenta": template_name,
        "versiya_shablona": template_version,
        "otvetstvennye_rukovoditeli": responsible,
        "proizvoditeli_rabot": producer,
        "ispolniteli": performer,
        "chleny_brigady": brigade_member,
        "dopuskayushchie": admitting,
        "nablyudayushchie": "",
        "prochie_uchastniki": "",
        "uchastniki_rabot": all_participants,
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
