"""Admin registrations for the documents app."""

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .forms import DocumentTemplateAdminForm
from .models import DocumentTemplate, GeneratedDocument
from .services import DOCX_TEMPLATE_ERROR_MESSAGE, generate_template_demo_docx


TEMPLATE_VARIABLES = [
    {"variable": "{{ номер_наряда }}", "description": "Номер наряда-допуска", "example": "ND-2026-001"},
    {"variable": "{{ статус_наряда }}", "description": "Текущий статус наряда", "example": "Draft"},
    {"variable": "{{ участок }}", "description": "Участок выполнения работ", "example": "Цех 1"},
    {"variable": "{{ оборудование }}", "description": "Оборудование", "example": "Насос H-101"},
    {"variable": "{{ вид_работ }}", "description": "Вид работ", "example": "Огневые работы"},
    {"variable": "{{ место_работ }}", "description": "Место выполнения работ", "example": "Площадка обслуживания"},
    {"variable": "{{ описание_работ }}", "description": "Описание выполняемых работ", "example": "Ремонт запорной арматуры"},
    {"variable": "{{ характер_работ }}", "description": "Характер нестандартных работ", "example": "Осмотр и ремонт арматуры"},
    {"variable": "{{ дополнительные_условия }}", "description": "Дополнительные условия и уточнения", "example": "Работы выполнять после инструктажа"},
    {"variable": "{{ дополнительные_меры_безопасности }}", "description": "Дополнительные меры безопасности", "example": "Использовать диэлектрические перчатки"},
    {"variable": "{{ дата_начала }}", "description": "Дата начала работ", "example": "13.06.2026"},
    {"variable": "{{ дата_окончания }}", "description": "Дата окончания работ", "example": "13.06.2026"},
    {"variable": "{{ дата_создания }}", "description": "Дата создания наряда", "example": "12.06.2026"},
    {"variable": "{{ ответственный_руководитель }}", "description": "Ответственный руководитель", "example": "Иванов И.И."},
    {"variable": "{{ производитель_работ }}", "description": "Производитель работ", "example": "Петров П.П."},
    {"variable": "{{ создал_пользователь }}", "description": "Пользователь, создавший наряд", "example": "operator"},
    {"variable": "{{ опасности }}", "description": "Список опасностей через запятую", "example": "Высота, Электрическое напряжение"},
    {"variable": "{{ меры_безопасности }}", "description": "Список мер безопасности через запятую", "example": "Ограждение, СИЗ"},
]

TEMPLATE_VARIABLE_RULES = [
    "не ставить пробел между фигурными скобками.",
    "писать переменные строго как в таблице.",
    "не разрывать переменную переносом строки.",
    "не форматировать часть переменной отдельно.",
]


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    form = DocumentTemplateAdminForm
    change_list_template = "admin/documents/documenttemplate/change_list.html"
    list_display = ("name", "document_type", "version", "is_active", "uploaded_by", "created_at", "test_template_link")
    list_filter = ("document_type", "is_active", "created_at")
    search_fields = ("name", "document_type", "version")
    readonly_fields = ("created_at",)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "template-variables/",
                self.admin_site.admin_view(self.template_variables_view),
                name="documents_documenttemplate_template_variables",
            ),
            path(
                "<int:template_id>/test/",
                self.admin_site.admin_view(self.test_template_view),
                name="documents_documenttemplate_test",
            ),
        ]
        return custom_urls + urls

    def template_variables_view(self, request):
        context = {
            **self.admin_site.each_context(request),
            "title": "Переменные DOCX-шаблона",
            "template_variables": TEMPLATE_VARIABLES,
            "rules": TEMPLATE_VARIABLE_RULES,
            "opts": self.model._meta,
        }
        return TemplateResponse(
            request,
            "admin/documents/documenttemplate/template_variables.html",
            context,
        )


    @admin.display(description="Проверка")
    def test_template_link(self, obj):
        url = reverse("admin:documents_documenttemplate_test", args=[obj.pk])
        return format_html('<a class="button" href="{}">Проверить шаблон</a>', url)

    def test_template_view(self, request, template_id):
        try:
            content, filename = generate_template_demo_docx(template_id)
        except ValidationError:
            messages.error(request, DOCX_TEMPLATE_ERROR_MESSAGE)
            return TemplateResponse(
                request,
                "admin/documents/documenttemplate/template_test_error.html",
                {
                    **self.admin_site.each_context(request),
                    "title": "Ошибка проверки DOCX-шаблона",
                    "opts": self.model._meta,
                    "message": DOCX_TEMPLATE_ERROR_MESSAGE,
                },
                status=200,
            )

        response = HttpResponse(
            content,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    list_display = ("permit", "template", "generated_by", "created_at")
    list_filter = ("created_at", "template__document_type")
    search_fields = ("permit__number", "template__name", "generated_by__username")
    readonly_fields = ("created_at",)
