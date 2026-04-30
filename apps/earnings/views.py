from itertools import groupby

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EarningForm
from .models import Earning
from .services import generate_allocations


def _save_form(form: EarningForm, *, user) -> Earning:
    """Persist a form-built earning. Month and receiver are set on the
    instance by ``EarningForm.clean()``; we just stamp ``created_by`` and
    regenerate the allocations."""
    earning = form.save(commit=False)
    if earning.created_by_id is None:
        earning.created_by = user
    earning.save()
    generate_allocations(earning)
    return earning


@login_required
def earning_list(request):
    add_form = EarningForm()
    if request.method == "POST":
        add_form = EarningForm(request.POST)
        if add_form.is_valid():
            _save_form(add_form, user=request.user)
            messages.success(request, "Earning recorded.")
            return redirect("earnings:list")

    earnings = list(
        Earning.objects
        .select_related("month", "earner", "receiver_person", "created_by")
        .order_by("-month__year", "-month__month", "-received_on", "-id")
    )
    grouped = [
        (month, list(rows))
        for month, rows in groupby(earnings, key=lambda e: e.month)
    ]
    return render(
        request,
        "earnings/list.html",
        {"grouped": grouped, "add_form": add_form},
    )


@login_required
def earning_detail(request, pk: int):
    earning = get_object_or_404(
        Earning.objects.select_related("month", "earner", "receiver_person"),
        pk=pk,
    )
    return render(request, "earnings/detail.html", {"earning": earning})


@login_required
def earning_edit(request, pk: int):
    earning = get_object_or_404(Earning, pk=pk)
    if not earning.month.is_editable:
        messages.error(request, "That month is closed; reopen it to edit earnings.")
        return redirect("earnings:detail", pk=earning.pk)
    if request.method == "POST":
        form = EarningForm(request.POST, instance=earning)
        if form.is_valid():
            _save_form(form, user=request.user)
            messages.success(request, "Earning updated.")
            return redirect("earnings:detail", pk=earning.pk)
    else:
        form = EarningForm(instance=earning)
    return render(request, "earnings/form.html", {"form": form, "earning": earning})
