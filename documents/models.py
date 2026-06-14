"""Models for the documents app."""

from django.conf import settings
from django.db import models


class DocumentTemplate(models.Model):
    """DOCX template uploaded for permit document generation."""

    name = models.CharField("Название", max_length=255)
    document_type = models.CharField("Тип документа", max_length=64)
    version = models.CharField("Версия", max_length=32)
    file = models.FileField("Файл DOCX-шаблона", upload_to="document_templates/")
    is_active = models.BooleanField("Активен", default=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_document_templates",
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "DOCX-шаблон"
        verbose_name_plural = "DOCX-шаблоны"
        ordering = ["document_type", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["document_type", "version"],
                name="unique_document_template_version",
            )
        ]

    def __str__(self):
        return f"{self.name} v{self.version}"


class GeneratedDocument(models.Model):
    """Generated DOCX/PDF files for a permit."""

    permit = models.ForeignKey(
        "permits.Permit",
        on_delete=models.CASCADE,
        related_name="generated_documents",
    )
    template = models.ForeignKey(
        DocumentTemplate,
        on_delete=models.PROTECT,
        related_name="generated_documents",
    )
    file_docx = models.FileField("Файл DOCX", upload_to="generated_documents/docx/")
    file_pdf = models.FileField("Файл PDF", upload_to="generated_documents/pdf/", blank=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="generated_documents",
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Сформированный документ"
        verbose_name_plural = "Сформированные документы"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.permit} — {self.template}"
