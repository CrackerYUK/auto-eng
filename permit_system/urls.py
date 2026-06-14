"""URL configuration for the permit_system project."""

from django.contrib import admin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import include, path

from permits import views as permit_views


def healthcheck(_request):
    """Return a small response for local Docker health checks."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("", lambda _request: redirect("permits:dashboard"), name="home"),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("health/", healthcheck, name="healthcheck"),
    path("permits/", include("permits.urls")),
    path("personnel/search/", permit_views.personnel_search, name="personnel_search"),
]
