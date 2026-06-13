"""Admin registrations for the documents app."""

from django.contrib import admin

from .models import DocumentTemplate, GeneratedDocument


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "document_type", "version", "is_active", "uploaded_by", "created_at")
    list_filter = ("document_type", "is_active", "created_at")
    search_fields = ("name", "document_type", "version")
    readonly_fields = ("created_at",)


@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    list_display = ("permit", "template", "generated_by", "created_at")
    list_filter = ("created_at", "template__document_type")
    search_fields = ("permit__number", "template__name", "generated_by__username")
    readonly_fields = ("created_at",)
