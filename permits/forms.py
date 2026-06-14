"""Forms for permit create and edit pages."""

from django import forms

from permits.models import Equipment, Hazard, Permit, SafetyMeasure, WorkArea, WorkType


class PermitForm(forms.ModelForm):
    """Form for creating and editing the main Permit fields."""

    class Meta:
        model = Permit
        fields = [
            "number",
            "work_starts_at",
            "work_ends_at",
            "work_location",
            "responsible_manager_text",
            "work_producer_text",
            "work_nature_text",
            "additional_conditions",
            "additional_safety_notes",
            "work_area",
            "equipment",
            "work_type",
            "hazards",
            "safety_measures",
            "work_description",
            "responsible_manager",
            "work_supervisor",
        ]
        labels = {
            "responsible_manager_text": "Ответственный руководитель работ (ручной ввод)",
            "work_producer_text": "Производитель работ (ручной ввод)",
            "work_nature_text": "Характер работ",
            "additional_conditions": "Дополнительные условия / уточнения",
            "additional_safety_notes": "Дополнительные меры безопасности / примечания",
        }
        widgets = {
            "work_starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "work_ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "hazards": forms.CheckboxSelectMultiple(),
            "safety_measures": forms.CheckboxSelectMultiple(),
            "work_description": forms.Textarea(attrs={"rows": 4}),
            "additional_conditions": forms.Textarea(attrs={"rows": 3}),
            "additional_safety_notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["work_area"].queryset = WorkArea.objects.filter(is_active=True)
        self.fields["equipment"].queryset = Equipment.objects.filter(is_active=True)
        self.fields["work_type"].queryset = WorkType.objects.filter(is_active=True)
        self.fields["hazards"].queryset = Hazard.objects.filter(is_active=True)
        self.fields["safety_measures"].queryset = SafetyMeasure.objects.filter(is_active=True)
