from itertools import groupby

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

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
    add_form = EarningForm(form_id="form-add")
    if request.method == "POST":
        add_form = EarningForm(request.POST, form_id="form-add")
        if add_form.is_valid():
            _save_form(add_form, user=request.user)
            messages.success(request, "Earning recorded.")
            return redirect("earnings:list")

    edit_pk = request.GET.get("edit")
    edit_form = None
    edit_obj = None
    if edit_pk and edit_pk.isdigit():
        edit_obj = Earning.objects.filter(pk=int(edit_pk)).select_related("month").first()
        if edit_obj and edit_obj.month.is_editable:
            edit_form = EarningForm(instance=edit_obj, form_id="form-edit")
        else:
            edit_obj = None

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
        {
            "grouped": grouped,
            "add_form": add_form,
            "edit_form": edit_form,
            "edit_pk": edit_obj.pk if edit_obj else None,
        },
    )


@require_POST
@login_required
def earning_update(request, pk: int):
    earning = get_object_or_404(Earning, pk=pk)
    if not earning.month.is_editable:
        messages.error(request, "That month is closed; reopen it to edit earnings.")
        return redirect("earnings:list")
    form = EarningForm(request.POST, instance=earning, form_id="form-edit")
    if form.is_valid():
        _save_form(form, user=request.user)
        messages.success(request, "Earning updated.")
        return redirect("earnings:list")
    # Re-render the list with this row in edit mode and the errors visible.
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
        {
            "grouped": grouped,
            "add_form": EarningForm(form_id="form-add"),
            "edit_form": form,
            "edit_pk": earning.pk,
        },
    )


@require_POST
@login_required
def earning_delete(request, pk: int):
    earning = get_object_or_404(Earning.objects.select_related("month"), pk=pk)
    if not earning.month.is_editable:
        messages.error(request, "That month is closed; reopen it to delete earnings.")
        return redirect("earnings:list")
    label = f"{earning.earner} · {earning.amount}"
    earning.delete()
    messages.success(request, f"Deleted earning ({label}).")
    return redirect("earnings:list")


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
