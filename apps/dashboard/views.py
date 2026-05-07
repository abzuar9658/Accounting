from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from apps.periods.models import Month

from .services import dashboard_context, entity_income_by_month, monthly_report


@login_required
def dashboard(request):
    return render(request, "dashboard/index.html", dashboard_context())


@login_required
def report(request, code: str):
    month = get_object_or_404(Month, year=int(code[:4]), month=int(code[5:7]))
    return render(request, "dashboard/report.html", monthly_report(month))


@login_required
def entity_income(request):
    return render(
        request,
        "dashboard/entity_income.html",
        {"entity_income": entity_income_by_month(limit=None)},
    )
