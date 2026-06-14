"""Views for the minimal permit web interface."""

from datetime import timezone as datetime_timezone

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Q
from django.http import FileResponse, Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from approvals.models import ApprovalAction
from audit.models import AuditLog
from approvals.services import (
    TRANSITION_APPROVE_BY_CHIEF,
    TRANSITION_APPROVE_BY_MASTER,
    TRANSITION_CLOSE,
    TRANSITION_REJECT,
    TRANSITION_RETURN,
    TRANSITION_SUBMIT,
    can_apply_transition,
    approve_by_chief,
    approve_by_master,
    close_permit,
    reject_permit,
    return_permit,
    submit_permit,
)
from documents.models import DocumentTemplate, GeneratedDocument
from documents.services import PdfConversionError, convert_docx_to_pdf, generate_permit_docx
from permits.forms import PermitForm, PermitParticipantFormSet
from permits.models import Permit, PermitParticipantRole, PermitStatus, Personnel
from users.roles import ROLE_CHIEF, ROLE_MASTER, ROLE_OPERATOR


ACTION_HANDLERS = {
    TRANSITION_SUBMIT: submit_permit,
    TRANSITION_RETURN: return_permit,
    TRANSITION_APPROVE_BY_MASTER: approve_by_master,
    TRANSITION_APPROVE_BY_CHIEF: approve_by_chief,
    TRANSITION_REJECT: reject_permit,
    TRANSITION_CLOSE: close_permit,
}

ACTION_LABELS = {
    TRANSITION_SUBMIT: "Отправить на проверку",
    TRANSITION_RETURN: "Вернуть на доработку",
    TRANSITION_APPROVE_BY_MASTER: "Согласовать мастером",
    TRANSITION_APPROVE_BY_CHIEF: "Утвердить начальником",
    TRANSITION_REJECT: "Отклонить",
    TRANSITION_CLOSE: "Закрыть",
}

EDITABLE_STATUSES = {PermitStatus.DRAFT, PermitStatus.RETURNED}
DOCX_GENERATION_STATUSES = {PermitStatus.APPROVED_BY_CHIEF, PermitStatus.CLOSED}
PENDING_STATUSES_BY_ROLE = {
    ROLE_OPERATOR: PermitStatus.RETURNED,
    ROLE_MASTER: PermitStatus.SUBMITTED,
    ROLE_CHIEF: PermitStatus.APPROVED_BY_MASTER,
}


class DashboardView(LoginRequiredMixin, TemplateView):
    """Display permit counts, recent permits and current-user pending work."""

    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        status_counts = {status: 0 for status in PermitStatus.values}
        status_counts.update(
            {
                row["status"]: row["count"]
                for row in Permit.objects.values("status").annotate(count=Count("id"))
            }
        )
        pending_statuses = [
            status
            for role_name, status in PENDING_STATUSES_BY_ROLE.items()
            if self.request.user.groups.filter(name=role_name).exists()
        ]
        pending_permits = Permit.objects.none()
        if pending_statuses:
            pending_permits = Permit.objects.filter(status__in=pending_statuses)

        context["status_counts"] = [
            {"status": status, "label": label, "count": status_counts[status]}
            for status, label in PermitStatus.choices
        ]
        context["recent_permits"] = Permit.objects.select_related(
            "created_by",
            "work_area",
            "equipment",
            "work_type",
        )[:10]
        context["pending_permits"] = pending_permits.select_related(
            "created_by",
            "work_area",
            "equipment",
            "work_type",
        )[:10]
        context["quick_links"] = self._quick_links()
        return context

    def _quick_links(self):
        links = [
            {"label": "Создать наряд", "url": reverse("permits:create")},
            {"label": "Список нарядов", "url": reverse("permits:list")},
        ]
        if _is_staff_or_admin(self.request.user):
            links.extend(
                [
                    {
                        "label": "Шаблоны DOCX",
                        "url": reverse("admin:documents_documenttemplate_changelist"),
                    },
                    {
                        "label": "Справочники",
                        "url": reverse("admin:permits_workarea_changelist"),
                    },
                    {"label": "Админка", "url": reverse("admin:index")},
                ]
            )
        return links


class PermitListView(LoginRequiredMixin, ListView):
    """Display a table with permits."""

    model = Permit
    template_name = "permits/permit_list.html"
    context_object_name = "permits"
    paginate_by = 50
    queryset = Permit.objects.select_related(
        "created_by",
        "work_area",
        "equipment",
        "work_type",
    )


class PermitDetailView(LoginRequiredMixin, DetailView):
    """Display one permit with approval history and generated documents."""

    model = Permit
    template_name = "permits/permit_detail.html"
    context_object_name = "permit"
    queryset = Permit.objects.select_related(
        "responsible_manager",
        "work_supervisor",
        "created_by",
        "work_area",
        "equipment",
        "work_type",
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        permit = self.object
        context["approval_actions"] = ApprovalAction.objects.filter(permit=permit).select_related(
            "actor"
        )
        context["generated_documents"] = GeneratedDocument.objects.filter(permit=permit).select_related(
            "template",
            "generated_by",
        )
        context["permit_change_logs"] = AuditLog.objects.filter(
            object_type="Permit",
            object_id=str(permit.pk),
            action__in=["permit.created", "permit.updated"],
        ).select_related("user")
        context["available_actions"] = [
            {"name": action, "label": ACTION_LABELS[action]}
            for action in ACTION_HANDLERS
            if can_apply_transition(permit, self.request.user, action)
        ]
        context["can_edit"] = permit.status in EDITABLE_STATUSES
        context["can_generate_docx"] = can_generate_permit_docx(permit, self.request.user)
        context["can_generate_pdf"] = can_manage_generated_document(permit, self.request.user)
        context["participant_groups"] = group_permit_participants(permit)
        return context


class PermitParticipantFormSetMixin:
    """Attach permit participant inline formsets to create/update views."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "participant_formset" not in context:
            if self.request.method == "POST":
                context["participant_formset"] = PermitParticipantFormSet(
                    self.request.POST,
                    instance=getattr(self, "object", None),
                )
            else:
                context["participant_formset"] = PermitParticipantFormSet(
                    instance=getattr(self, "object", None),
                )
        return context

    def form_invalid(self, form):
        return self.render_to_response(
            self.get_context_data(
                form=form,
                participant_formset=PermitParticipantFormSet(
                    self.request.POST,
                    instance=getattr(self, "object", None),
                ),
            )
        )


class PermitCreateView(LoginRequiredMixin, PermitParticipantFormSetMixin, CreateView):
    """Create a draft permit."""

    model = Permit
    form_class = PermitForm
    template_name = "permits/permit_form.html"

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.status = PermitStatus.DRAFT
        self.object.created_by = self.request.user
        participant_formset = PermitParticipantFormSet(self.request.POST, instance=self.object)
        if not participant_formset.is_valid():
            return self.render_to_response(
                self.get_context_data(form=form, participant_formset=participant_formset)
            )
        self.object.save()
        form.save_m2m()
        participant_formset.instance = self.object
        participant_formset.save()
        create_permit_audit_log(self.object, self.request.user)
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy("permits:detail", kwargs={"pk": self.object.pk})


class PermitUpdateView(LoginRequiredMixin, PermitParticipantFormSetMixin, UpdateView):
    """Edit a permit only while it is draft or returned."""

    model = Permit
    form_class = PermitForm
    template_name = "permits/permit_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.status not in EDITABLE_STATUSES:
            return HttpResponseForbidden("Наряд можно редактировать только в статусе черновика или возврата на доработку.")
        if request.method == "POST":
            self._audit_old_values = capture_permit_audit_values(self.object)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        old_values = self._audit_old_values
        self.object = form.save(commit=False)
        participant_formset = PermitParticipantFormSet(self.request.POST, instance=self.object)
        if not participant_formset.is_valid():
            return self.render_to_response(
                self.get_context_data(form=form, participant_formset=participant_formset)
            )
        self.object.save()
        form.save_m2m()
        participant_formset.save()
        new_values = capture_permit_audit_values(self.object)
        create_permit_update_audit_log(
            self.object,
            self.request.user,
            old_values,
            new_values,
        )
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy("permits:detail", kwargs={"pk": self.object.pk})


@login_required
@require_POST
def permit_action(request, pk, action):
    """Run an approval action from the permit card."""
    permit = get_object_or_404(Permit, pk=pk)
    handler = ACTION_HANDLERS.get(action)
    if handler is None:
        return HttpResponseForbidden("Неизвестное действие с нарядом.")

    if not can_apply_transition(permit, request.user, action):
        messages.error(request, "Действие недоступно для вашей роли или текущего статуса наряда.")
        return HttpResponseForbidden("Действие с нарядом недоступно.")

    try:
        handler(permit, request.user, request.POST.get("comment", ""))
    except (PermissionDenied, ValidationError) as exc:
        messages.error(request, exc)
    else:
        messages.success(request, f"Действие «{ACTION_LABELS[action]}» выполнено.")
    return redirect("permits:detail", pk=permit.pk)


@login_required
@require_POST
def generate_docx(request, pk):
    """Generate a DOCX document for a permit using the active permit template."""
    permit = get_object_or_404(Permit, pk=pk)
    if not can_generate_permit_docx(permit, request.user):
        messages.error(request, "Формирование DOCX недоступно для этого статуса наряда.")
        return HttpResponseForbidden("Формирование DOCX недоступно.")

    template = (
        DocumentTemplate.objects.filter(document_type="permit", is_active=True)
        .order_by("-created_at", "-id")
        .first()
    )
    if template is None:
        messages.error(request, "Активный DOCX-шаблон для нарядов не настроен.")
        return redirect("permits:detail", pk=permit.pk)

    generated_document = generate_permit_docx(
        permit_id=permit.pk,
        template_id=template.pk,
        user=request.user,
    )
    messages.success(request, "DOCX-документ успешно сформирован. Ссылка для скачивания доступна ниже.")
    return redirect("permits:detail", pk=permit.pk)


@login_required
def download_generated_document(request, pk):
    """Download a generated DOCX document if the user is allowed to access it."""
    generated_document = get_object_or_404(
        GeneratedDocument.objects.select_related(
            "permit__created_by",
            "permit__responsible_manager",
            "permit__work_supervisor",
            "generated_by",
        ),
        pk=pk,
    )
    if not can_download_generated_document(generated_document, request.user):
        raise Http404("Сформированный документ не найден.")

    if not generated_document.file_docx:
        raise Http404("Сформированный DOCX-файл не найден.")

    return FileResponse(
        generated_document.file_docx.open("rb"),
        as_attachment=True,
        filename=generated_document.file_docx.name.rsplit("/", 1)[-1],
    )


@login_required
@require_POST
def generate_pdf(request, pk):
    """Generate a PDF from an existing generated DOCX document."""
    generated_document = get_object_or_404(
        GeneratedDocument.objects.select_related(
            "permit__created_by",
            "permit__responsible_manager",
            "permit__work_supervisor",
            "generated_by",
        ),
        pk=pk,
    )
    if not can_manage_generated_document(generated_document.permit, request.user):
        return HttpResponseForbidden("Формирование PDF недоступно.")

    try:
        convert_docx_to_pdf(generated_document.pk)
    except PdfConversionError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "PDF-документ успешно сформирован. Ссылка для скачивания доступна ниже.")
    return redirect("permits:detail", pk=generated_document.permit.pk)


@login_required
def download_generated_pdf(request, pk):
    """Download a generated PDF document if the user is allowed to access it."""
    generated_document = get_object_or_404(
        GeneratedDocument.objects.select_related(
            "permit__created_by",
            "permit__responsible_manager",
            "permit__work_supervisor",
            "generated_by",
        ),
        pk=pk,
    )
    if not can_download_generated_document(generated_document, request.user):
        raise Http404("Сформированный документ не найден.")

    if not generated_document.file_pdf:
        raise Http404("Сформированный PDF-файл не найден.")

    return FileResponse(
        generated_document.file_pdf.open("rb"),
        as_attachment=True,
        filename=generated_document.file_pdf.name.rsplit("/", 1)[-1],
    )


@login_required
def personnel_search(request):
    """Return active personnel options for lightweight local autocomplete/search."""
    query = request.GET.get("q", "").strip()
    personnel = Personnel.objects.filter(is_active=True).select_related("group", "work_area")
    if query:
        personnel = personnel.filter(
            Q(full_name__icontains=query)
            | Q(personnel_number__icontains=query)
            | Q(position__icontains=query)
            | Q(group__name__icontains=query)
        )
    results = [{"id": item.pk, "label": str(item)} for item in personnel[:20]]
    return JsonResponse({"results": results})


def group_permit_participants(permit):
    """Group permit participants for detail-page display."""
    labels = {
        PermitParticipantRole.RESPONSIBLE_MANAGER: "Ответственные руководители",
        PermitParticipantRole.WORK_PRODUCER: "Производители работ",
        PermitParticipantRole.PERFORMER: "Исполнители",
        PermitParticipantRole.BRIGADE_MEMBER: "Члены бригады",
        PermitParticipantRole.ADMITTING_PERSON: "Допускающие",
        PermitParticipantRole.OBSERVER: "Наблюдающие",
        PermitParticipantRole.OTHER: "Прочие",
    }
    grouped = {role: [] for role in labels}
    participants = permit.participants.select_related(
        "personnel",
        "personnel__group",
        "personnel__work_area",
    )
    for participant in participants:
        grouped.setdefault(participant.role, []).append(participant)
    return [
        {"role": role, "label": label, "participants": grouped.get(role, [])}
        for role, label in labels.items()
    ]


def can_generate_permit_docx(permit, user):
    """Return whether the user can generate DOCX for the permit."""
    if not user.is_authenticated or permit.status not in DOCX_GENERATION_STATUSES:
        return False
    return _is_staff_or_admin(user) or user.groups.filter(
        name__in=(ROLE_OPERATOR, ROLE_CHIEF),
    ).exists()


def can_download_generated_document(generated_document, user):
    """Return whether the user can download a generated document."""
    return can_manage_generated_document(generated_document.permit, user)


def can_manage_generated_document(permit, user):
    """Return whether the user can access generated documents for a permit."""
    return user.is_authenticated and (
        _is_staff_or_admin(user) or user.has_perm("permits.view_permit")
    )


def _is_staff_or_admin(user):
    return (
        user.is_authenticated
        and (
            user.is_staff
            or user.is_superuser
            or user.groups.filter(name="admin").exists()
        )
    )


PERMIT_AUDIT_FIELDS = (
    "number",
    "status",
    "work_starts_at",
    "work_ends_at",
    "work_location",
    "responsible_manager_text",
    "work_producer_text",
    "work_nature_text",
    "additional_conditions",
    "additional_safety_notes",
    "work_area",
    "equipment",
    "work_type",
    "hazards",
    "safety_measures",
    "work_description",
    "responsible_manager",
    "work_supervisor",
)

PERMIT_AUDIT_M2M_FIELDS = {"hazards", "safety_measures"}

PERMIT_AUDIT_FK_FIELDS = {
    "work_area",
    "equipment",
    "work_type",
    "responsible_manager",
    "work_supervisor",
}


def capture_permit_audit_values(permit):
    """Capture JSON-serializable permit values for audit comparison."""
    values = {}
    for field_name in PERMIT_AUDIT_FIELDS:
        if field_name in PERMIT_AUDIT_M2M_FIELDS:
            values[field_name] = _serialize_m2m_field(permit, field_name)
        elif field_name in PERMIT_AUDIT_FK_FIELDS:
            values[field_name] = _serialize_fk_value(getattr(permit, field_name))
        else:
            values[field_name] = _serialize_plain_value(getattr(permit, field_name))
    return values


def create_permit_audit_log(permit, user):
    """Write an audit log for permit creation."""
    AuditLog.objects.create(
        user=user,
        action="permit.created",
        object_type="Permit",
        object_id=str(permit.pk),
        details={
            "old_values": {},
            "new_values": capture_permit_audit_values(permit),
        },
    )


def create_permit_update_audit_log(permit, user, old_values, new_values):
    """Write an audit log with changed fields only when actual values changed."""
    changes = {
        field_name: {"old": old_values[field_name], "new": new_values[field_name]}
        for field_name in PERMIT_AUDIT_FIELDS
        if old_values[field_name] != new_values[field_name]
    }
    if not changes:
        return None

    return AuditLog.objects.create(
        user=user,
        action="permit.updated",
        object_type="Permit",
        object_id=str(permit.pk),
        details={
            "old_values": old_values,
            "new_values": new_values,
            "changes": changes,
        },
    )


def _serialize_m2m_field(permit, field_name):
    return [
        {"id": item.pk, "label": str(item)}
        for item in getattr(permit, field_name).order_by("pk")
    ]


def _serialize_fk_value(value):
    if value is None:
        return None
    return {"id": value.pk, "label": str(value)}


def _serialize_plain_value(value):
    if value is None:
        return None
    if hasattr(value, "astimezone"):
        return value.astimezone(datetime_timezone.utc).isoformat()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value
