"""Tests for permit approval workflow services."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from approvals.models import ApprovalAction
from approvals.services import (
    approve_by_chief,
    approve_by_master,
    close_permit,
    reject_permit,
    return_permit,
    submit_permit,
)
from audit.models import AuditLog
from permits.models import Permit, PermitStatus, WorkArea, WorkType
from users.roles import ROLE_CHIEF, ROLE_MASTER, ROLE_OPERATOR


class ApprovalServiceTests(TestCase):
    """Checks for valid transitions, invalid transitions, and role restrictions."""

    @classmethod
    def setUpTestData(cls):
        call_command("setup_roles", verbosity=0)
        user_model = get_user_model()
        cls.operator = user_model.objects.create_user(username="operator")
        cls.master = user_model.objects.create_user(username="master")
        cls.chief = user_model.objects.create_user(username="chief")
        cls.plain_user = user_model.objects.create_user(username="plain")
        cls.operator.groups.add(Group.objects.get(name=ROLE_OPERATOR))
        cls.master.groups.add(Group.objects.get(name=ROLE_MASTER))
        cls.chief.groups.add(Group.objects.get(name=ROLE_CHIEF))
        cls.work_area = WorkArea.objects.create(name="Workshop 1")
        cls.work_type = WorkType.objects.create(name="Hot work")

    def make_permit(self, number="PT-SVC-001", status=PermitStatus.DRAFT):
        starts_at = timezone.now() + timedelta(days=1)
        return Permit.objects.create(
            number=number,
            status=status,
            work_starts_at=starts_at,
            work_ends_at=starts_at + timedelta(hours=8),
            work_location="Workshop 1",
            work_area=self.work_area,
            work_type=self.work_type,
            work_description="Hot work preparation",
            responsible_manager=self.master,
            work_supervisor=self.operator,
            created_by=self.operator,
        )

    def test_full_valid_approval_flow_creates_actions_and_audit_logs(self):
        permit = self.make_permit()

        submit_action = submit_permit(permit, self.operator, "submit for review")
        approve_master_action = approve_by_master(permit, self.master, "master approved")
        approve_chief_action = approve_by_chief(permit, self.chief, "chief approved")
        close_action = close_permit(permit, self.operator, "work completed")

        permit.refresh_from_db()
        self.assertEqual(permit.status, PermitStatus.CLOSED)
        self.assertEqual(submit_action.old_status, PermitStatus.DRAFT)
        self.assertEqual(submit_action.new_status, PermitStatus.SUBMITTED)
        self.assertEqual(approve_master_action.new_status, PermitStatus.APPROVED_BY_MASTER)
        self.assertEqual(approve_chief_action.new_status, PermitStatus.APPROVED_BY_CHIEF)
        self.assertEqual(close_action.new_status, PermitStatus.CLOSED)
        self.assertEqual(ApprovalAction.objects.filter(permit=permit).count(), 4)
        self.assertEqual(AuditLog.objects.filter(object_id=str(permit.pk)).count(), 4)

    def test_return_permit_valid_transition(self):
        permit = self.make_permit(number="PT-SVC-002", status=PermitStatus.SUBMITTED)

        action = return_permit(permit, self.master, "needs corrections")

        permit.refresh_from_db()
        self.assertEqual(permit.status, PermitStatus.RETURNED)
        self.assertEqual(action.old_status, PermitStatus.SUBMITTED)
        self.assertEqual(action.new_status, PermitStatus.RETURNED)
        self.assertEqual(action.comment, "needs corrections")

    def test_reject_permit_valid_transition(self):
        permit = self.make_permit(number="PT-SVC-003", status=PermitStatus.APPROVED_BY_MASTER)

        action = reject_permit(permit, self.chief, "unsafe work conditions")

        permit.refresh_from_db()
        self.assertEqual(permit.status, PermitStatus.REJECTED)
        self.assertEqual(action.old_status, PermitStatus.APPROVED_BY_MASTER)
        self.assertEqual(action.new_status, PermitStatus.REJECTED)

    def test_invalid_status_transition_does_not_create_action_or_audit_log(self):
        permit = self.make_permit(number="PT-SVC-004", status=PermitStatus.DRAFT)

        with self.assertRaises(ValidationError):
            approve_by_master(permit, self.master, "too early")

        permit.refresh_from_db()
        self.assertEqual(permit.status, PermitStatus.DRAFT)
        self.assertFalse(ApprovalAction.objects.filter(permit=permit).exists())
        self.assertFalse(AuditLog.objects.filter(object_id=str(permit.pk)).exists())

    def test_invalid_role_does_not_create_action_or_audit_log(self):
        permit = self.make_permit(number="PT-SVC-005", status=PermitStatus.SUBMITTED)

        with self.assertRaises(PermissionDenied):
            approve_by_master(permit, self.operator, "operator cannot master approve")

        permit.refresh_from_db()
        self.assertEqual(permit.status, PermitStatus.SUBMITTED)
        self.assertFalse(ApprovalAction.objects.filter(permit=permit).exists())
        self.assertFalse(AuditLog.objects.filter(object_id=str(permit.pk)).exists())

    def test_user_without_role_cannot_submit(self):
        permit = self.make_permit(number="PT-SVC-006")

        with self.assertRaises(PermissionDenied):
            submit_permit(permit, self.plain_user, "no role")

        permit.refresh_from_db()
        self.assertEqual(permit.status, PermitStatus.DRAFT)
