"""Project URL configuration."""
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.accounts.urls")),
    path("company/", include("apps.company.urls")),
    path(
        "",
        login_required(TemplateView.as_view(template_name="home.html")),
        name="dashboard",
    ),
]
