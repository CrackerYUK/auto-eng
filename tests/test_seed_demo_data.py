"""Tests for the demo data management command."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase

from documents.models import DocumentTemplate
from permits.models import (
    Equipment,
    Hazard,
    Permit,
    PermitParticipant,
    Personnel,
    PersonnelGroup,
    SafetyMeasure,
    WorkArea,
    WorkType,
)
from users.roles import ROLE_ADMIN, ROLE_CHIEF, ROLE_MASTER, ROLE_OPERATOR


class SeedDemoDataCommandTests(TestCase):
    """Checks that local demo data can be created safely."""

    def test_seed_demo_data_runs_without_error(self):
        call_command("seed_demo_data", verbosity=0)

        user_model = get_user_model()
        for username, role_name in (
            ("operator", ROLE_OPERATOR),
            ("master", ROLE_MASTER),
            ("chief", ROLE_CHIEF),
            ("admin", ROLE_ADMIN),
        ):
            user = user_model.objects.get(username=username)
            self.assertTrue(user.groups.filter(name=role_name).exists())

        self.assertTrue(Group.objects.filter(name=ROLE_OPERATOR).exists())
        self.assertGreaterEqual(WorkArea.objects.count(), 2)
        self.assertGreaterEqual(Equipment.objects.count(), 2)
        self.assertGreaterEqual(WorkType.objects.count(), 2)
        self.assertGreaterEqual(Hazard.objects.count(), 1)
        self.assertGreaterEqual(SafetyMeasure.objects.count(), 1)
        self.assertGreaterEqual(Permit.objects.count(), 4)
        self.assertGreaterEqual(PersonnelGroup.objects.count(), 5)
        self.assertGreaterEqual(Personnel.objects.count(), 5)
        self.assertGreaterEqual(PermitParticipant.objects.count(), 1)
        self.assertFalse(user_model.objects.filter(username="D-1001").exists())
        self.assertTrue(
            DocumentTemplate.objects.filter(
                document_type="permit",
                version="demo-translit-1",
            ).exists()
        )
