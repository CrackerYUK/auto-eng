"""Template filters for Permit status presentation."""

from django import template

from permits.models import PermitStatus


register = template.Library()


STATUS_BADGE_CLASSES = {
    PermitStatus.DRAFT: "status-badge status-draft",
    PermitStatus.SUBMITTED: "status-badge status-submitted",
    PermitStatus.RETURNED: "status-badge status-returned",
    PermitStatus.APPROVED_BY_MASTER: "status-badge status-approved-by-master",
    PermitStatus.APPROVED_BY_CHIEF: "status-badge status-approved-by-chief",
    PermitStatus.REJECTED: "status-badge status-rejected",
    PermitStatus.CLOSED: "status-badge status-closed",
    PermitStatus.ARCHIVED: "status-badge status-archived",
}


@register.filter
def permit_status_label(status):
    """Return the human-readable label for a Permit status value."""
    return PermitStatus(status).label if status in PermitStatus.values else status


@register.filter
def permit_status_badge_class(status):
    """Return CSS classes for a Permit status badge."""
    return STATUS_BADGE_CLASSES.get(status, "status-badge status-unknown")
