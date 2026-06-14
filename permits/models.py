"""Models for the permits app."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class ActiveDirectoryModel(models.Model):
    """Base model for simple active/inactive reference directories."""

    name = models.CharField("Название", max_length=255, unique=True)
    description = models.TextField("Описание", blank=True)
    is_active = models.BooleanField("Активно", default=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self):
        return self.name


class WorkArea(ActiveDirectoryModel):
    """Work area or facility where permit work is performed."""

    class Meta(ActiveDirectoryModel.Meta):
        verbose_name = "Участок"
        verbose_name_plural = "Участки"


class Equipment(models.Model):
    """Equipment within a work area."""

    name = models.CharField("Название", max_length=255)
    code = models.CharField("Код", max_length=128)
    work_area = models.ForeignKey(
        WorkArea,
        on_delete=models.PROTECT,
        related_name="equipment",
    )
    description = models.TextField("Описание", blank=True)
    is_active = models.BooleanField("Активно", default=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Оборудование"
        verbose_name_plural = "Оборудование"
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

    class Meta(ActiveDirectoryModel.Meta):
        verbose_name = "Вид работ"
        verbose_name_plural = "Виды работ"


class Hazard(ActiveDirectoryModel):
    """Hazard that may be present during permit work."""

    class Meta(ActiveDirectoryModel.Meta):
        verbose_name = "Опасность"
        verbose_name_plural = "Опасности"


class SafetyMeasure(ActiveDirectoryModel):
    """Safety measure required for permit work."""

    class Meta(ActiveDirectoryModel.Meta):
        verbose_name = "Мера безопасности"
        verbose_name_plural = "Меры безопасности"


class PersonnelGroup(ActiveDirectoryModel):
    """Directory group for non-user personnel records."""

    class Meta(ActiveDirectoryModel.Meta):
        verbose_name = "Группа персонала"
        verbose_name_plural = "Группы персонала"


class Personnel(models.Model):
    """Worker directory entry that is not an authentication user."""

    full_name = models.CharField("ФИО", max_length=255)
    personnel_number = models.CharField("Табельный номер", max_length=64, blank=True)
    position = models.CharField("Должность", max_length=255, blank=True)
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
    department = models.CharField("Подразделение", max_length=255, blank=True)
    phone = models.CharField("Телефон", max_length=64, blank=True)
    notes = models.TextField("Примечания", blank=True)
    is_active = models.BooleanField("Активно", default=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Работник"
        verbose_name_plural = "Персонал"
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

    DRAFT = "draft", "Черновик"
    SUBMITTED = "submitted", "Отправлен мастеру"
    RETURNED = "returned", "Возвращён на доработку"
    APPROVED_BY_MASTER = "approved_by_master", "Согласован мастером"
    APPROVED_BY_CHIEF = "approved_by_chief", "Утверждён начальником"
    REJECTED = "rejected", "Отклонён"
    CLOSED = "closed", "Закрыт"
    ARCHIVED = "archived", "В архиве"


class Permit(models.Model):
    """Work permit with core scheduling and responsibility information."""

    number = models.CharField("Номер", max_length=64, unique=True)
    status = models.CharField(
        "Статус",
        max_length=32,
        choices=PermitStatus.choices,
        default=PermitStatus.DRAFT,
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    work_starts_at = models.DateTimeField("Начало работ")
    work_ends_at = models.DateTimeField("Окончание работ")
    work_location = models.CharField("Место работ", max_length=255)
    responsible_manager_text = models.CharField(
        "Ответственный руководитель работ (ручной ввод)",
        max_length=255,
        blank=True,
    )
    work_producer_text = models.CharField(
        "Производитель работ (ручной ввод)",
        max_length=255,
        blank=True,
    )
    work_nature_text = models.CharField(
        "Характер работ",
        max_length=255,
        blank=True,
    )
    additional_conditions = models.TextField(
        "Дополнительные условия",
        blank=True,
    )
    additional_safety_notes = models.TextField(
        "Дополнительные меры безопасности",
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
    work_description = models.TextField("Описание работ")
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
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Наряд-допуск"
        verbose_name_plural = "Наряды-допуски"
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
    manual_name = models.CharField("Ручной ввод участника", max_length=255, blank=True)
    note = models.CharField("Примечание", max_length=255, blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Участник наряда"
        verbose_name_plural = "Участники наряда"
        ordering = ["sort_order", "id"]

    def clean(self):
        super().clean()
        if self.personnel_id is None and not (self.manual_name or "").strip():
            raise ValidationError("Выберите работника из справочника или укажите участника вручную.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def display_name(self):
        if self.personnel_id:
            name_parts = [self.personnel.full_name]
            if self.personnel.position:
                name_parts.append(self.personnel.position)
            if self.personnel.group_id:
                name_parts.append(self.personnel.group.name)
            name = " — ".join(name_parts)
        else:
            name = (self.manual_name or "").strip()
        if self.note:
            return f"{name} ({self.note})"
        return name

    def __str__(self):
        return f"{self.get_role_display()}: {self.display_name()}"
