"""Create non-production demo data for local permit-system demonstrations."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from permits.models import (
    Equipment,
    Hazard,
    Permit,
    PermitStatus,
    SafetyMeasure,
    WorkArea,
    WorkType,
)
from users.roles import ROLE_ADMIN, ROLE_CHIEF, ROLE_MASTER, ROLE_OPERATOR


DEMO_PASSWORD = "demo12345"


class Command(BaseCommand):
    """Create idempotent local demo users, directories and permits."""

    help = "Create non-production demo data for local permit-system demonstrations."

    def handle(self, *args, **options):
        call_command("setup_roles", verbosity=0)

        users = self._create_users()
        demo_data = self._create_directories()
        self._create_permits(users, demo_data)

        if options["verbosity"] > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "Demo data is ready. Demo users use password "
                    f"'{DEMO_PASSWORD}'. Do not use this data in production."
                )
            )

    def _create_users(self):
        user_model = get_user_model()
        user_specs = {
            "operator": {
                "groups": [ROLE_OPERATOR],
                "is_staff": False,
                "is_superuser": False,
            },
            "master": {
                "groups": [ROLE_MASTER],
                "is_staff": False,
                "is_superuser": False,
            },
            "chief": {
                "groups": [ROLE_CHIEF],
                "is_staff": False,
                "is_superuser": False,
            },
            "admin": {
                "groups": [ROLE_ADMIN],
                "is_staff": True,
                "is_superuser": True,
            },
        }
        users = {}
        for username, spec in user_specs.items():
            user, _created = user_model.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@example.local",
                    "is_staff": spec["is_staff"],
                    "is_superuser": spec["is_superuser"],
                },
            )
            user.email = f"{username}@example.local"
            user.is_staff = spec["is_staff"]
            user.is_superuser = spec["is_superuser"]
            user.set_password(DEMO_PASSWORD)
            user.save()
            user.groups.set(Group.objects.filter(name__in=spec["groups"]))
            users[username] = user
        return users

    def _create_directories(self):
        work_area_main, _created = WorkArea.objects.get_or_create(
            name="Demo workshop",
            defaults={"description": "Non-production demo workshop."},
        )
        work_area_boiler, _created = WorkArea.objects.get_or_create(
            name="Demo boiler house",
            defaults={"description": "Non-production demo boiler house."},
        )
        pump, _created = Equipment.objects.get_or_create(
            work_area=work_area_main,
            code="DEMO-PUMP-01",
            defaults={
                "name": "Demo circulation pump",
                "description": "Demo equipment for local presentations.",
            },
        )
        boiler, _created = Equipment.objects.get_or_create(
            work_area=work_area_boiler,
            code="DEMO-BOILER-01",
            defaults={
                "name": "Demo boiler unit",
                "description": "Demo boiler equipment for local presentations.",
            },
        )
        inspection, _created = WorkType.objects.get_or_create(
            name="Demo inspection",
            defaults={"description": "Inspection work for local demonstrations."},
        )
        repair, _created = WorkType.objects.get_or_create(
            name="Demo repair",
            defaults={"description": "Repair work for local demonstrations."},
        )
        pressure, _created = Hazard.objects.get_or_create(
            name="Demo pressure hazard",
            defaults={"description": "Non-production pressure hazard."},
        )
        lockout, _created = SafetyMeasure.objects.get_or_create(
            name="Demo lockout/tagout",
            defaults={"description": "Non-production lockout/tagout measure."},
        )
        return {
            "work_area_main": work_area_main,
            "work_area_boiler": work_area_boiler,
            "pump": pump,
            "boiler": boiler,
            "inspection": inspection,
            "repair": repair,
            "pressure": pressure,
            "lockout": lockout,
        }

    def _create_permits(self, users, demo_data):
        now = timezone.now().replace(second=0, microsecond=0)
        permit_specs = [
            {
                "number": "DEMO-DRAFT-001",
                "status": PermitStatus.DRAFT,
                "starts_in": 1,
                "work_location": "Demo workshop pump room",
                "work_area": demo_data["work_area_main"],
                "equipment": demo_data["pump"],
                "work_type": demo_data["inspection"],
                "work_description": "Demo draft permit for pump inspection.",
            },
            {
                "number": "DEMO-SUBMITTED-001",
                "status": PermitStatus.SUBMITTED,
                "starts_in": 2,
                "work_location": "Demo boiler house platform",
                "work_area": demo_data["work_area_boiler"],
                "equipment": demo_data["boiler"],
                "work_type": demo_data["repair"],
                "work_description": "Demo submitted permit awaiting master review.",
            },
            {
                "number": "DEMO-APPROVED-001",
                "status": PermitStatus.APPROVED_BY_CHIEF,
                "starts_in": 3,
                "work_location": "Demo workshop maintenance bay",
                "work_area": demo_data["work_area_main"],
                "equipment": demo_data["pump"],
                "work_type": demo_data["repair"],
                "work_description": "Demo approved permit ready for DOCX generation.",
            },
            {
                "number": "DEMO-RETURNED-001",
                "status": PermitStatus.RETURNED,
                "starts_in": 4,
                "work_location": "Demo boiler house service area",
                "work_area": demo_data["work_area_boiler"],
                "equipment": demo_data["boiler"],
                "work_type": demo_data["inspection"],
                "work_description": "Demo returned permit for correction.",
            },
        ]
        for spec in permit_specs:
            starts_at = now + timedelta(days=spec["starts_in"])
            permit, _created = Permit.objects.update_or_create(
                number=spec["number"],
                defaults={
                    "status": spec["status"],
                    "work_starts_at": starts_at,
                    "work_ends_at": starts_at + timedelta(hours=8),
                    "work_location": spec["work_location"],
                    "work_area": spec["work_area"],
                    "equipment": spec["equipment"],
                    "work_type": spec["work_type"],
                    "work_description": spec["work_description"],
                    "responsible_manager": users["chief"],
                    "work_supervisor": users["master"],
                    "created_by": users["operator"],
                },
            )
            permit.hazards.set([demo_data["pressure"]])
            permit.safety_measures.set([demo_data["lockout"]])
