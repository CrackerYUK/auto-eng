"""Create baseline Django groups and permissions for permit-system roles."""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError

from users.roles import LOCAL_PERMISSION_APP_LABELS, ROLE_ADMIN, ROLE_NAMES, ROLE_PERMISSIONS


class Command(BaseCommand):
    """Create or update the baseline role groups."""

    help = "Create permit-system role groups and assign their baseline permissions."

    def handle(self, *args, **options):
        for role_name in ROLE_NAMES:
            group, created = Group.objects.get_or_create(name=role_name)
            permissions = self._permissions_for_role(role_name)
            group.permissions.set(permissions)
            if options["verbosity"] > 0:
                state = "created" if created else "updated"
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Role group '{role_name}' {state} with {len(permissions)} permissions."
                    )
                )

    def _permissions_for_role(self, role_name):
        if role_name == ROLE_ADMIN:
            return Permission.objects.filter(
                content_type__app_label__in=LOCAL_PERMISSION_APP_LABELS
            ).order_by("content_type__app_label", "codename")

        permission_specs = ROLE_PERMISSIONS.get(role_name, ())
        permissions = []
        for app_label, model, codename in permission_specs:
            permissions.append(self._get_permission(app_label, model, codename))
        return permissions

    def _get_permission(self, app_label, model, codename):
        try:
            content_type = ContentType.objects.get(app_label=app_label, model=model)
            return Permission.objects.get(content_type=content_type, codename=codename)
        except (ContentType.DoesNotExist, Permission.DoesNotExist) as exc:
            raise CommandError(
                "Required permission is missing. Run migrations before setup_roles: "
                f"{app_label}.{codename}"
            ) from exc
