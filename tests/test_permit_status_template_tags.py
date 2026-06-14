"""Tests for Permit status template filters."""

from django.test import SimpleTestCase

from permits.models import PermitStatus
from permits.templatetags.permit_status import (
    permit_status_badge_class,
    permit_status_label,
)


class PermitStatusTemplateTagTests(SimpleTestCase):
    """Checks human-readable labels and badge CSS classes for statuses."""

    def test_permit_status_label_returns_human_readable_label(self):
        self.assertEqual(
            permit_status_label(PermitStatus.APPROVED_BY_CHIEF),
            "Approved by chief",
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
