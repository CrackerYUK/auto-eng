"""Tests for Permit status template filters."""

from django.test import SimpleTestCase

from permits.models import PermitStatus
from permits.templatetags.permit_status import (
    approval_action_label,
    audit_field_label,
    permit_status_badge_class,
    permit_status_label,
)


class PermitStatusTemplateTagTests(SimpleTestCase):
    """Checks human-readable labels and badge CSS classes for statuses."""

    def test_permit_status_label_returns_human_readable_label(self):
        self.assertEqual(
            permit_status_label(PermitStatus.APPROVED_BY_CHIEF),
            "Утверждён начальником",
        )

    def test_permit_status_label_preserves_unknown_status(self):
        self.assertEqual(permit_status_label("unknown_status"), "unknown_status")

    def test_permit_status_badge_class_returns_status_specific_class(self):
        self.assertEqual(
            permit_status_badge_class(PermitStatus.RETURNED),
            "status-badge status-returned",
        )

    def test_permit_status_badge_class_returns_unknown_class(self):
        self.assertEqual(
            permit_status_badge_class("unknown_status"),
            "status-badge status-unknown",
        )

    def test_approval_action_label_returns_human_readable_label(self):
        self.assertEqual(approval_action_label("submit"), "Отправлен мастеру")
        self.assertEqual(approval_action_label("return"), "Возвращён на доработку")
        self.assertEqual(approval_action_label("approve_by_master"), "Согласован мастером")
        self.assertEqual(approval_action_label("approve_by_chief"), "Утверждён начальником")
        self.assertEqual(approval_action_label("reject"), "Отклонён")
        self.assertEqual(approval_action_label("close"), "Закрыт")

    def test_approval_action_label_preserves_unknown_action(self):
        self.assertEqual(approval_action_label("custom_action"), "custom_action")

    def test_audit_field_label_returns_human_readable_label(self):
        self.assertEqual(audit_field_label("status"), "Статус")
        self.assertEqual(audit_field_label("number"), "Номер наряда")
        self.assertEqual(audit_field_label("work_location"), "Место проведения работ")

    def test_audit_field_label_preserves_unknown_field(self):
        self.assertEqual(audit_field_label("custom_field"), "custom_field")
