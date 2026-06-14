"""Admin registrations for the permits app."""

from django.contrib import admin

from .models import (
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


@admin.register(WorkArea)
class WorkAreaAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "work_area", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "work_area")
    search_fields = ("name", "code", "description", "work_area__name")


@admin.register(WorkType)
class WorkTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")


@admin.register(Hazard)
class HazardAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")


@admin.register(SafetyMeasure)
class SafetyMeasureAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")


@admin.register(PersonnelGroup)
class PersonnelGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")


@admin.register(Personnel)
class PersonnelAdmin(admin.ModelAdmin):
    list_display = ("full_name", "position", "group", "work_area", "is_active")
    list_filter = ("group", "is_active", "work_area")
    search_fields = ("full_name", "personnel_number", "position", "group__name")


class PermitParticipantInline(admin.TabularInline):
    model = PermitParticipant
    extra = 1
    fields = ("role", "personnel", "manual_name", "note", "sort_order")
    autocomplete_fields = ("personnel",)


@admin.register(Permit)
class PermitAdmin(admin.ModelAdmin):
    inlines = (PermitParticipantInline,)
    list_display = (
        "number",
        "status",
        "work_location",
        "work_area",
        "equipment",
        "work_type",
        "responsible_manager",
        "work_supervisor",
        "work_starts_at",
        "work_ends_at",
        "created_by",
    )
    list_filter = (
        "status",
        "work_area",
        "equipment",
        "work_type",
        "hazards",
        "safety_measures",
        "work_starts_at",
        "work_ends_at",
    )
    search_fields = (
        "number",
        "work_location",
        "work_description",
        "work_area__name",
        "equipment__name",
        "equipment__code",
        "work_type__name",
    )
    readonly_fields = ("created_at", "updated_at")
    filter_horizontal = ("hazards", "safety_measures")


@admin.register(PermitParticipant)
class PermitParticipantAdmin(admin.ModelAdmin):
    list_display = ("permit", "role", "personnel", "manual_name", "sort_order")
    list_filter = ("role", "personnel__group")
    search_fields = (
        "permit__number",
        "personnel__full_name",
        "personnel__personnel_number",
        "manual_name",
        "note",
    )
    autocomplete_fields = ("permit", "personnel")
