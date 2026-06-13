"""Tests for baseline role setup."""

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase

from users.roles import ROLE_ADMIN, ROLE_CHIEF, ROLE_MASTER, ROLE_NAMES, ROLE_OPERATOR


class SetupRolesCommandTests(TestCase):
    """Checks for the setup_roles management command."""

    def test_setup_roles_creates_expected_groups(self):
        call_command("setup_roles", verbosity=0)

        group_names = set(Group.objects.values_list("name", flat=True))
        self.assertTrue(set(ROLE_NAMES).issubset(group_names))

    def test_setup_roles_assigns_baseline_permissions(self):
        call_command("setup_roles", verbosity=0)

        operator = Group.objects.get(name=ROLE_OPERATOR)
        master = Group.objects.get(name=ROLE_MASTER)
        chief = Group.objects.get(name=ROLE_CHIEF)
        admin = Group.objects.get(name=ROLE_ADMIN)

        operator_permissions = set(operator.permissions.values_list("codename", flat=True))
        master_permissions = set(master.permissions.values_list("codename", flat=True))
        chief_permissions = set(chief.permissions.values_list("codename", flat=True))
        admin_permissions = set(admin.permissions.values_list("codename", flat=True))

        self.assertIn("add_permit", operator_permissions)
        self.assertIn("change_permit", operator_permissions)
        self.assertIn("add_approvalaction", master_permissions)
        self.assertIn("add_approvalaction", chief_permissions)
        self.assertIn("delete_permit", admin_permissions)
        self.assertIn("view_auditlog", admin_permissions)
