"""Project URL configuration."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path

from apps.dashboard.views import dashboard as dashboard_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.accounts.urls")),
    path("company/", include("apps.company.urls")),
    path("months/", include("apps.periods.urls")),
    path("earnings/", include("apps.earnings.urls")),
    path("expenses/", include("apps.expenses.urls")),
    path("transfers/", include("apps.transfers.urls")),
    path("audit/", include("apps.audit.urls")),
    path("reports/", include("apps.dashboard.urls")),
    path("", login_required(dashboard_view), name="dashboard"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
