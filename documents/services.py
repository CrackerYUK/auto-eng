"""Document generation services."""

from io import BytesIO
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from docxtpl import DocxTemplate

from documents.models import DocumentTemplate, GeneratedDocument
from permits.models import Permit


class PdfConversionError(RuntimeError):
    """Raised when DOCX to PDF conversion cannot be completed safely."""


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
    docx_template.render(_build_permit_context(permit))

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


def _build_permit_context(permit):
    return {
        "permit": {
            "id": permit.pk,
            "number": permit.number,
            "status": permit.status,
            "status_display": permit.get_status_display(),
            "created_at": permit.created_at,
            "work_starts_at": permit.work_starts_at,
            "work_ends_at": permit.work_ends_at,
            "work_location": permit.work_location,
            "work_area": permit.work_area,
            "work_area_name": permit.work_area.name,
            "equipment": permit.equipment,
            "equipment_name": permit.equipment.name if permit.equipment else "",
            "equipment_code": permit.equipment.code if permit.equipment else "",
            "work_type": permit.work_type,
            "work_type_name": permit.work_type.name,
            "hazards": list(permit.hazards.all()),
            "hazard_names": [hazard.name for hazard in permit.hazards.all()],
            "hazard_names_text": ", ".join(hazard.name for hazard in permit.hazards.all()),
            "safety_measures": list(permit.safety_measures.all()),
            "safety_measure_names": [measure.name for measure in permit.safety_measures.all()],
            "safety_measure_names_text": ", ".join(
                measure.name for measure in permit.safety_measures.all()
            ),
            "work_description": permit.work_description,
            "responsible_manager": permit.responsible_manager,
            "responsible_manager_name": permit.responsible_manager.get_username(),
            "work_supervisor": permit.work_supervisor,
            "work_supervisor_name": permit.work_supervisor.get_username(),
            "created_by": permit.created_by,
            "created_by_name": permit.created_by.get_username(),
            "updated_at": permit.updated_at,
        }
    }


def _generated_docx_name(permit, template):
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    return f"permit_{permit.number}_template_{template.pk}_{timestamp}.docx"


def _generated_pdf_name(generated_document):
    docx_name = Path(generated_document.file_docx.name).stem
    return f"{docx_name}.pdf"
