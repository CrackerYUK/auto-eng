"""Models for the permits app."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class ActiveDirectoryModel(models.Model):
    """Base model for simple active/inactive reference directories."""

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self):
        return self.name


class WorkArea(ActiveDirectoryModel):
    """Work area or facility where permit work is performed."""


class Equipment(models.Model):
    """Equipment within a work area."""

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=128)
    work_area = models.ForeignKey(
        WorkArea,
        on_delete=models.PROTECT,
        related_name="equipment",
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["work_area", "code"],
                name="unique_equipment_code_per_work_area",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"


class WorkType(ActiveDirectoryModel):
    """Type of work covered by a permit."""


class Hazard(ActiveDirectoryModel):
    """Hazard that may be present during permit work."""


class SafetyMeasure(ActiveDirectoryModel):
    """Safety measure required for permit work."""


class PersonnelGroup(ActiveDirectoryModel):
    """Directory group for non-user personnel records."""


class Personnel(models.Model):
    """Worker directory entry that is not an authentication user."""

    full_name = models.CharField(max_length=255)
    personnel_number = models.CharField(max_length=64, blank=True)
    position = models.CharField(max_length=255, blank=True)
    group = models.ForeignKey(
        PersonnelGroup,
        on_delete=models.PROTECT,
        related_name="personnel",
    )
    work_area = models.ForeignKey(
        WorkArea,
        on_delete=models.PROTECT,
        related_name="personnel",
        null=True,
        blank=True,
    )
    department = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=64, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["full_name", "personnel_number"]

    def __str__(self):
        parts = [self.full_name]
        if self.position:
            parts.append(self.position)
        if self.group_id:
            parts.append(self.group.name)
        if self.work_area_id:
            parts.append(self.work_area.name)
        return " — ".join(parts)


class PermitStatus(models.TextChoices):
    """Lifecycle statuses for a permit."""

    DRAFT = "draft", "Draft"
    SUBMITTED = "submitted", "Submitted"
    RETURNED = "returned", "Returned"
    APPROVED_BY_MASTER = "approved_by_master", "Approved by master"
    APPROVED_BY_CHIEF = "approved_by_chief", "Approved by chief"
    REJECTED = "rejected", "Rejected"
    CLOSED = "closed", "Closed"
    ARCHIVED = "archived", "Archived"


class Permit(models.Model):
    """Work permit with core scheduling and responsibility information."""

    number = models.CharField(max_length=64, unique=True)
    status = models.CharField(
        max_length=32,
        choices=PermitStatus.choices,
        default=PermitStatus.DRAFT,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    work_starts_at = models.DateTimeField()
    work_ends_at = models.DateTimeField()
    work_location = models.CharField(max_length=255)
    responsible_manager_text = models.CharField(
        "responsible manager free-text value",
        max_length=255,
        blank=True,
    )
    work_producer_text = models.CharField(
        "work producer free-text value",
        max_length=255,
        blank=True,
    )
    work_nature_text = models.CharField(
        "work nature free-text value",
        max_length=255,
        blank=True,
    )
    additional_conditions = models.TextField(
        "additional conditions",
        blank=True,
    )
    additional_safety_notes = models.TextField(
        "additional safety notes",
        blank=True,
    )
    work_area = models.ForeignKey(
        WorkArea,
        on_delete=models.PROTECT,
        related_name="permits",
    )
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.PROTECT,
        related_name="permits",
        null=True,
        blank=True,
    )
    work_type = models.ForeignKey(
        WorkType,
        on_delete=models.PROTECT,
        related_name="permits",
    )
    hazards = models.ManyToManyField(Hazard, related_name="permits", blank=True)
    safety_measures = models.ManyToManyField(
        SafetyMeasure,
        related_name="permits",
        blank=True,
    )
    work_description = models.TextField()
    responsible_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="managed_permits",
    )
    work_supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="supervised_permits",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_permits",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "number"]

    def __str__(self):
        return self.number


class PermitParticipantRole(models.TextChoices):
    """Participant roles used inside a permit."""

    RESPONSIBLE_MANAGER = "responsible_manager", "Ответственный руководитель работ"
    WORK_PRODUCER = "work_producer", "Производитель работ"
    PERFORMER = "performer", "Исполнитель работ"
    BRIGADE_MEMBER = "brigade_member", "Член бригады"
    ADMITTING_PERSON = "admitting_person", "Допускающий"
    OBSERVER = "observer", "Наблюдающий"
    OTHER = "other", "Другое"


class PermitParticipant(models.Model):
    """Flexible participant row for a permit."""

    permit = models.ForeignKey(
        Permit,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    role = models.CharField(
        max_length=64,
        choices=PermitParticipantRole.choices,
        default=PermitParticipantRole.PERFORMER,
    )
    personnel = models.ForeignKey(
        Personnel,
        on_delete=models.PROTECT,
        related_name="permit_participations",
        null=True,
        blank=True,
    )
    manual_name = models.CharField(max_length=255, blank=True)
    note = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def clean(self):
        super().clean()
        if self.personnel_id is None and not (self.manual_name or "").strip():
            raise ValidationError("Choose personnel or enter manual participant name.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def display_name(self):
        if self.personnel_id:
            name = self.personnel.full_name
            if self.personnel.position:
                name = f"{name} — {self.personnel.position}"
        else:
            name = (self.manual_name or "").strip()
        if self.note:
            return f"{name} ({self.note})"
        return name

    def __str__(self):
        return f"{self.get_role_display()}: {self.display_name()}"
