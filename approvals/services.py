"""Approval workflow services for permits."""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from approvals.models import ApprovalAction
from audit.models import AuditLog
from permits.models import PermitStatus
from users.roles import ROLE_ADMIN, ROLE_CHIEF, ROLE_MASTER, ROLE_OPERATOR


TRANSITION_SUBMIT = "submit"
TRANSITION_RETURN = "return"
TRANSITION_APPROVE_BY_MASTER = "approve_by_master"
TRANSITION_APPROVE_BY_CHIEF = "approve_by_chief"
TRANSITION_REJECT = "reject"
TRANSITION_CLOSE = "close"


TRANSITIONS = {
    TRANSITION_SUBMIT: {
        "from": {PermitStatus.DRAFT, PermitStatus.RETURNED},
        "to": PermitStatus.SUBMITTED,
        "roles": {ROLE_OPERATOR, ROLE_ADMIN},
    },
    TRANSITION_RETURN: {
        "from": {PermitStatus.SUBMITTED, PermitStatus.APPROVED_BY_MASTER},
        "to": PermitStatus.RETURNED,
        "roles": {ROLE_MASTER, ROLE_CHIEF, ROLE_ADMIN},
    },
    TRANSITION_APPROVE_BY_MASTER: {
        "from": {PermitStatus.SUBMITTED},
        "to": PermitStatus.APPROVED_BY_MASTER,
        "roles": {ROLE_MASTER, ROLE_ADMIN},
    },
    TRANSITION_APPROVE_BY_CHIEF: {
        "from": {PermitStatus.APPROVED_BY_MASTER},
        "to": PermitStatus.APPROVED_BY_CHIEF,
        "roles": {ROLE_CHIEF, ROLE_ADMIN},
    },
    TRANSITION_REJECT: {
        "from": {PermitStatus.SUBMITTED, PermitStatus.APPROVED_BY_MASTER},
        "to": PermitStatus.REJECTED,
        "roles": {ROLE_MASTER, ROLE_CHIEF, ROLE_ADMIN},
    },
    TRANSITION_CLOSE: {
        "from": {PermitStatus.APPROVED_BY_CHIEF},
        "to": PermitStatus.CLOSED,
        "roles": {ROLE_OPERATOR, ROLE_CHIEF, ROLE_ADMIN},
    },
}


def can_apply_transition(permit, user, transition_name):
    """Return whether a user can apply a transition to the current permit state."""
    transition = TRANSITIONS.get(transition_name)
    if transition is None:
        return False
    return permit.status in transition["from"] and _user_has_allowed_role(
        user,
        transition["roles"],
    )


def submit_permit(permit, user, comment=""):
    """Submit a draft or returned permit for approval."""
    return _apply_transition(permit, user, TRANSITION_SUBMIT, comment)


def return_permit(permit, user, comment=""):
    """Return a submitted permit to the operator for corrections."""
    return _apply_transition(permit, user, TRANSITION_RETURN, comment)


def approve_by_master(permit, user, comment=""):
    """Approve a submitted permit by master."""
    return _apply_transition(permit, user, TRANSITION_APPROVE_BY_MASTER, comment)


def approve_by_chief(permit, user, comment=""):
    """Approve a master-approved permit by chief."""
    return _apply_transition(permit, user, TRANSITION_APPROVE_BY_CHIEF, comment)


def reject_permit(permit, user, comment=""):
    """Reject a submitted or master-approved permit."""
    return _apply_transition(permit, user, TRANSITION_REJECT, comment)


def close_permit(permit, user, comment=""):
    """Close a fully approved permit."""
    return _apply_transition(permit, user, TRANSITION_CLOSE, comment)


@transaction.atomic
def _apply_transition(permit, user, transition_name, comment=""):
    transition = TRANSITIONS[transition_name]
    old_status = permit.status
    new_status = transition["to"]

    _validate_status_transition(transition_name, old_status, transition["from"])
    _validate_user_role(user, transition_name, transition["roles"])

    permit.status = new_status
    permit.save(update_fields=["status", "updated_at"])

    approval_action = ApprovalAction.objects.create(
        permit=permit,
        actor=user,
        action=transition_name,
        old_status=old_status,
        new_status=new_status,
        comment=comment,
    )
    AuditLog.objects.create(
        user=user,
        action=f"permit.{transition_name}",
        object_type=permit.__class__.__name__,
        object_id=str(permit.pk),
        details={
            "permit_number": permit.number,
            "old_status": old_status,
            "new_status": new_status,
            "comment": comment,
            "approval_action_id": approval_action.pk,
        },
    )
    return approval_action


def _validate_status_transition(transition_name, current_status, allowed_statuses):
    if current_status not in allowed_statuses:
        allowed = ", ".join(sorted(str(status) for status in allowed_statuses))
        raise ValidationError(
            f"Transition '{transition_name}' is not allowed from status "
            f"'{current_status}'. Allowed source statuses: {allowed}."
        )


def _validate_user_role(user, transition_name, allowed_roles):
    if _user_has_allowed_role(user, allowed_roles):
        return

    allowed = ", ".join(sorted(allowed_roles))
    raise PermissionDenied(
        f"User '{user}' cannot perform transition '{transition_name}'. "
        f"Required role: {allowed}."
    )


def _user_has_allowed_role(user, allowed_roles):
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name__in=allowed_roles).exists()
