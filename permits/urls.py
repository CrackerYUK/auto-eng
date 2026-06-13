"""URL routes for permit pages."""

from django.urls import path

from permits import views

app_name = "permits"

urlpatterns = [
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("", views.PermitListView.as_view(), name="list"),
    path("new/", views.PermitCreateView.as_view(), name="create"),
    path("<int:pk>/", views.PermitDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.PermitUpdateView.as_view(), name="edit"),
    path("<int:pk>/action/<str:action>/", views.permit_action, name="action"),
    path("<int:pk>/generate-docx/", views.generate_docx, name="generate_docx"),
    path(
        "documents/<int:pk>/download/",
        views.download_generated_document,
        name="download_document",
    ),
    path(
        "documents/<int:pk>/generate-pdf/",
        views.generate_pdf,
        name="generate_pdf",
    ),
    path(
        "documents/<int:pk>/download-pdf/",
        views.download_generated_pdf,
        name="download_pdf",
    ),
]
