"""Forms for permit create and edit pages."""

from django import forms
from django.contrib.auth import get_user_model

from permits.models import Equipment, Hazard, Permit, PermitStatus, SafetyMeasure, WorkArea, WorkType


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


class PermitFilterForm(forms.Form):
    """GET form for filtering the permit list."""

    status = forms.ChoiceField(
        choices=[("", "All statuses"), *PermitStatus.choices],
        required=False,
        label="Status",
    )
    work_area = forms.ModelChoiceField(
        queryset=WorkArea.objects.none(),
        required=False,
        label="Work area",
        empty_label="All work areas",
    )
    equipment = forms.ModelChoiceField(
        queryset=Equipment.objects.none(),
        required=False,
        label="Equipment",
        empty_label="All equipment",
    )
    work_type = forms.ModelChoiceField(
        queryset=WorkType.objects.none(),
        required=False,
        label="Work type",
        empty_label="All work types",
    )
    work_starts_from = forms.DateField(
        required=False,
        label="Work starts from",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    work_starts_to = forms.DateField(
        required=False,
        label="Work starts to",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    created_from = forms.DateField(
        required=False,
        label="Created from",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    created_to = forms.DateField(
        required=False,
        label="Created to",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    created_by = forms.ModelChoiceField(
        queryset=get_user_model().objects.none(),
        required=False,
        label="Author",
        empty_label="All authors",
    )
    q = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(attrs={"placeholder": "Number, location, description"}),
    )

    def __init__(self, *args, **kwargs):
        user_queryset = kwargs.pop("user_queryset")
        super().__init__(*args, **kwargs)
        self.fields["work_area"].queryset = WorkArea.objects.all()
        self.fields["equipment"].queryset = Equipment.objects.select_related("work_area")
        self.fields["work_type"].queryset = WorkType.objects.all()
        self.fields["created_by"].queryset = user_queryset
