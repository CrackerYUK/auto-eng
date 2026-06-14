"""Forms for validating uploaded document templates."""

from tempfile import NamedTemporaryFile

from django import forms
from docxtpl import DocxTemplate

from .models import DocumentTemplate
from .services import DOCX_TEMPLATE_ERROR_MESSAGE


class DocumentTemplateAdminForm(forms.ModelForm):
    """Validate uploaded DOCX templates before saving them from the admin."""

    class Meta:
        model = DocumentTemplate
        fields = "__all__"

    def clean_file(self):
        uploaded_file = self.cleaned_data["file"]
        if not uploaded_file.name.lower().endswith(".docx"):
            raise forms.ValidationError("Файл шаблона должен быть в формате .docx.")

        position = uploaded_file.tell() if hasattr(uploaded_file, "tell") else None
        try:
            with NamedTemporaryFile(suffix=".docx") as tmp_file:
                for chunk in uploaded_file.chunks():
                    tmp_file.write(chunk)
                tmp_file.flush()

                docx_template = DocxTemplate(tmp_file.name)
                docx_template.get_undeclared_template_variables()
                docx_template.render({})
        except Exception as exc:
            raise forms.ValidationError(DOCX_TEMPLATE_ERROR_MESSAGE) from exc
        finally:
            if position is not None:
                uploaded_file.seek(position)

        return uploaded_file
