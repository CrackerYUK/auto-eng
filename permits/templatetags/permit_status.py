"""Template filters for Permit status presentation."""

from django import template

from approvals.services import (
    TRANSITION_APPROVE_BY_CHIEF,
    TRANSITION_APPROVE_BY_MASTER,
    TRANSITION_CLOSE,
    TRANSITION_REJECT,
    TRANSITION_RETURN,
    TRANSITION_SUBMIT,
)
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

APPROVAL_ACTION_LABELS = {
    TRANSITION_SUBMIT: "Отправлен мастеру",
    TRANSITION_RETURN: "Возвращён на доработку",
    TRANSITION_APPROVE_BY_MASTER: "Согласован мастером",
    TRANSITION_APPROVE_BY_CHIEF: "Утверждён начальником",
    TRANSITION_REJECT: "Отклонён",
    TRANSITION_CLOSE: "Закрыт",
}

AUDIT_FIELD_LABELS = {
    "status": "Статус",
    "number": "Номер наряда",
    "work_area": "Участок",
    "equipment": "Оборудование",
    "work_type": "Вид работ",
    "work_location": "Место проведения работ",
    "work_location_text": "Место проведения работ",
    "work_nature_text": "Характер работ",
    "work_description": "Описание работ",
    "responsible_manager": "Ответственный руководитель",
    "responsible_manager_text": "Ответственный руководитель работ",
    "work_supervisor": "Производитель работ",
    "work_producer_text": "Производитель работ",
    "hazards": "Опасности",
    "safety_measures": "Меры безопасности",
    "additional_conditions": "Дополнительные условия",
    "additional_safety_notes": "Дополнительные меры безопасности",
    "work_starts_at": "Дата начала",
    "work_ends_at": "Дата окончания",
    "start_date": "Дата начала",
    "end_date": "Дата окончания",
    "created_by": "Создал",
    "updated_at": "Обновлено",
}


@register.filter
def permit_status_label(status):
    """Return the human-readable label for a Permit status value."""
    return PermitStatus(status).label if status in PermitStatus.values else status


@register.filter
def permit_status_badge_class(status):
    """Return CSS classes for a Permit status badge."""
    return STATUS_BADGE_CLASSES.get(status, "status-badge status-unknown")


@register.filter
def approval_action_label(action):
    """Return the user-facing label for an approval action value."""
    return APPROVAL_ACTION_LABELS.get(action, action)


@register.filter
def audit_field_label(field_name):
    """Return the user-facing label for an audit field name."""
    return AUDIT_FIELD_LABELS.get(field_name, field_name)
