from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from apps.periods.models import Month

from .services import dashboard_context, monthly_report


@login_required
def dashboard(request):
    return render(request, "dashboard/index.html", dashboard_context())


@login_required
def report(request, code: str):
    month = get_object_or_404(Month, year=int(code[:4]), month=int(code[5:7]))
    return render(request, "dashboard/report.html", monthly_report(month))
