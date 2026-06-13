"""Models for the permits app."""

from django.conf import settings
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
