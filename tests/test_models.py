"""Basic model tests for the permit-system domain entities."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from approvals.models import ApprovalAction
from audit.models import AuditLog
from documents.models import DocumentTemplate, GeneratedDocument
from permits.models import (
    Equipment,
    Hazard,
    Permit,
    PermitStatus,
    SafetyMeasure,
    WorkArea,
    WorkType,
)


class PermitSystemModelTests(TestCase):
    """Smoke tests for initial data models and their relationships."""

    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.creator = user_model.objects.create_user(username="creator")
        cls.manager = user_model.objects.create_user(username="manager")
        cls.supervisor = user_model.objects.create_user(username="supervisor")
        cls.actor = user_model.objects.create_user(username="actor")
        cls.work_area = WorkArea.objects.create(name="Workshop 1")
        cls.equipment = Equipment.objects.create(
            name="Pump A",
            code="P-100",
            work_area=cls.work_area,
        )
        cls.work_type = WorkType.objects.create(
            name="Hot work",
            description="Work involving ignition sources",
        )
        cls.hazard = Hazard.objects.create(
            name="Fire",
            description="Fire hazard",
        )
        cls.safety_measure = SafetyMeasure.objects.create(
            name="Fire watch",
            description="Assign a fire watcher",
        )
        cls.starts_at = timezone.now() + timedelta(days=1)
        cls.ends_at = cls.starts_at + timedelta(hours=8)
        cls.permit = Permit.objects.create(
            number="PT-001",
            work_starts_at=cls.starts_at,
            work_ends_at=cls.ends_at,
            work_location="Workshop 1",
            work_area=cls.work_area,
            equipment=cls.equipment,
            work_type=cls.work_type,
            work_description="Hot work preparation",
            responsible_manager=cls.manager,
            work_supervisor=cls.supervisor,
            created_by=cls.creator,
        )
        cls.permit.hazards.add(cls.hazard)
        cls.permit.safety_measures.add(cls.safety_measure)

    def test_permit_defaults_to_draft_status(self):
        self.assertEqual(self.permit.status, PermitStatus.DRAFT)
        self.assertEqual(str(self.permit), "PT-001")

    def test_permit_status_contains_required_values(self):
        values = {status.value for status in PermitStatus}
        self.assertEqual(
            values,
            {
                "draft",
                "submitted",
                "returned",
                "approved_by_master",
                "approved_by_chief",
                "rejected",
                "closed",
                "archived",
            },
        )

    def test_approval_action_tracks_status_change(self):
        action = ApprovalAction.objects.create(
            permit=self.permit,
            actor=self.actor,
            action="submit",
            old_status=PermitStatus.DRAFT,
            new_status=PermitStatus.SUBMITTED,
            comment="Ready for approval",
        )

        self.assertEqual(action.permit, self.permit)
        self.assertEqual(action.actor, self.actor)
        self.assertEqual(str(action), "PT-001 — submit")

    def test_document_template_and_generated_document(self):
        template = DocumentTemplate.objects.create(
            name="Default permit template",
            document_type="permit",
            version="1.0",
            file="templates/default.docx",
            uploaded_by=self.creator,
        )
        generated = GeneratedDocument.objects.create(
            permit=self.permit,
            template=template,
            file_docx="generated/pt-001.docx",
            file_pdf="generated/pt-001.pdf",
            generated_by=self.actor,
        )

        self.assertTrue(template.is_active)
        self.assertEqual(str(template), "Default permit template v1.0")
        self.assertEqual(generated.template, template)
        self.assertEqual(str(generated), "PT-001 — Default permit template v1.0")

    def test_audit_log_stores_action_details(self):
        log = AuditLog.objects.create(
            user=self.actor,
            action="permit.created",
            object_type="Permit",
            object_id=str(self.permit.pk),
            details={"number": self.permit.number},
        )

        self.assertEqual(log.details, {"number": "PT-001"})
        self.assertEqual(str(log), f"permit.created Permit:{self.permit.pk}")


    def test_permit_reference_directories_are_linked(self):
        self.assertEqual(str(self.work_area), "Workshop 1")
        self.assertEqual(str(self.equipment), "Pump A (P-100)")
        self.assertEqual(str(self.work_type), "Hot work")
        self.assertTrue(self.work_area.is_active)
        self.assertIsNotNone(self.work_area.created_at)
        self.assertIsNotNone(self.work_area.updated_at)
        self.assertTrue(self.equipment.is_active)
        self.assertEqual(self.equipment.code, "P-100")
        self.assertIsNotNone(self.equipment.created_at)
        self.assertIsNotNone(self.equipment.updated_at)
        self.assertEqual(self.permit.work_area, self.work_area)
        self.assertEqual(self.permit.equipment, self.equipment)
        self.assertEqual(self.permit.work_type, self.work_type)
        self.assertIn(self.hazard, self.permit.hazards.all())
        self.assertIn(self.safety_measure, self.permit.safety_measures.all())
