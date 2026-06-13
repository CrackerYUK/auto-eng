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
            "work_area",
            "equipment",
            "work_type",
            "hazards",
            "safety_measures",
            "work_description",
            "responsible_manager",
            "work_supervisor",
        ]
        widgets = {
            "work_starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "work_ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "hazards": forms.CheckboxSelectMultiple(),
            "safety_measures": forms.CheckboxSelectMultiple(),
            "work_description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["work_area"].queryset = WorkArea.objects.filter(is_active=True)
        self.fields["equipment"].queryset = Equipment.objects.filter(is_active=True)
        self.fields["work_type"].queryset = WorkType.objects.filter(is_active=True)
        self.fields["hazards"].queryset = Hazard.objects.filter(is_active=True)
        self.fields["safety_measures"].queryset = SafetyMeasure.objects.filter(is_active=True)
