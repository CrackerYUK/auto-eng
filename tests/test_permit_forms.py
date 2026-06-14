"""Tests for permit forms."""

from django.test import TestCase

from permits.forms import PermitForm, PermitParticipantForm
from permits.models import Equipment, Hazard, Personnel, PersonnelGroup, SafetyMeasure, WorkArea, WorkType


class PermitFormTests(TestCase):
    """Checks reference-directory fields in the permit form."""

    def test_permit_form_contains_reference_directory_fields(self):
        form = PermitForm()

        self.assertIn("work_area", form.fields)
        self.assertIn("equipment", form.fields)
        self.assertIn("work_type", form.fields)
        self.assertIn("hazards", form.fields)
        self.assertIn("safety_measures", form.fields)
        self.assertIn("responsible_manager_text", form.fields)
        self.assertIn("work_producer_text", form.fields)
        self.assertIn("work_nature_text", form.fields)
        self.assertIn("additional_conditions", form.fields)
        self.assertIn("additional_safety_notes", form.fields)

    def test_permit_form_uses_only_active_reference_values(self):
        active_area = WorkArea.objects.create(name="Active area")
        inactive_area = WorkArea.objects.create(name="Inactive area", is_active=False)
        active_equipment = Equipment.objects.create(
            name="Active equipment",
            code="AE-1",
            work_area=active_area,
        )
        inactive_equipment = Equipment.objects.create(
            name="Inactive equipment",
            code="IE-1",
            work_area=active_area,
            is_active=False,
        )
        active_work_type = WorkType.objects.create(name="Active work")
        inactive_work_type = WorkType.objects.create(name="Inactive work", is_active=False)
        active_hazard = Hazard.objects.create(name="Active hazard")
        inactive_hazard = Hazard.objects.create(name="Inactive hazard", is_active=False)
        active_measure = SafetyMeasure.objects.create(name="Active measure")
        inactive_measure = SafetyMeasure.objects.create(name="Inactive measure", is_active=False)

        form = PermitForm()

        self.assertIn(active_area, form.fields["work_area"].queryset)
        self.assertNotIn(inactive_area, form.fields["work_area"].queryset)
        self.assertIn(active_equipment, form.fields["equipment"].queryset)
        self.assertNotIn(inactive_equipment, form.fields["equipment"].queryset)
        self.assertIn(active_work_type, form.fields["work_type"].queryset)
        self.assertNotIn(inactive_work_type, form.fields["work_type"].queryset)
        self.assertIn(active_hazard, form.fields["hazards"].queryset)
        self.assertNotIn(inactive_hazard, form.fields["hazards"].queryset)
        self.assertIn(active_measure, form.fields["safety_measures"].queryset)
        self.assertNotIn(inactive_measure, form.fields["safety_measures"].queryset)


class PermitParticipantFormTests(TestCase):
    """Checks personnel selection in participant forms."""

    def test_participant_form_uses_only_active_personnel_with_context_label(self):
        work_area = WorkArea.objects.create(name="Area for personnel")
        group = PersonnelGroup.objects.create(name="Мастера")
        active = Personnel.objects.create(
            full_name="Иванов Иван Иванович",
            personnel_number="P-001",
            position="мастер",
            group=group,
            work_area=work_area,
        )
        inactive = Personnel.objects.create(
            full_name="Неактивный работник",
            position="слесарь",
            group=group,
            work_area=work_area,
            is_active=False,
        )

        form = PermitParticipantForm()

        self.assertIn(active, form.fields["personnel"].queryset)
        self.assertNotIn(inactive, form.fields["personnel"].queryset)
        label = form.fields["personnel"].label_from_instance(active)
        self.assertIn("Иванов Иван Иванович", label)
        self.assertIn("мастер", label)
        self.assertIn("Мастера", label)
        self.assertIn("Area for personnel", label)
