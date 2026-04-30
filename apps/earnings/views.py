from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.models import Person
from apps.periods.models import Month
from apps.transfers.services import settle_month_safe

from .forms import EarningCellForm, EarningForm
from .models import Earning
from .services import generate_allocations


def _save_form(form: EarningForm, *, user) -> Earning:
    """Persist a form-built earning. Month and receiver are set on the
    instance by ``EarningForm.clean()``; we stamp ``created_by``,
    regenerate the allocations and re-settle the affected month(s) so
    the transfer ledger never lags behind the source data."""
    previous_month = None
    if form.instance.pk:
        previous_month = (
            Earning.objects.filter(pk=form.instance.pk)
            .select_related("month").first()
        )
        previous_month = previous_month.month if previous_month else None
    earning = form.save(commit=False)
    if earning.created_by_id is None:
        earning.created_by = user
    earning.save()
    generate_allocations(earning)
    settle_month_safe(earning.month)
    if previous_month and previous_month.pk != (earning.month_id or 0):
        settle_month_safe(previous_month)
    return earning


def _build_pivot():
    """Group earnings by (project, earner) → row, with one cell per month.

    Months are returned in ascending chronological order so the column
    headers read naturally left-to-right (oldest first). Earnings whose
    month has been deleted (``month_id`` is null) are returned separately
    as ``orphans`` so the matrix stays clean.
    """
    earnings = list(
        Earning.objects
        .select_related("month", "earner")
        .order_by("month__year", "month__month", "project", "earner__name", "id")
    )
    orphans = [e for e in earnings if e.month_id is None]
    earnings = [e for e in earnings if e.month_id is not None]
    months_by_id = {e.month_id: e.month for e in earnings}
    months = sorted(months_by_id.values(), key=lambda m: (m.year, m.month))

    row_map: dict[tuple[str, int], dict] = {}
    for e in earnings:
        norm = (e.project or "").strip().lower()
        key = (norm, e.earner_id)
        row = row_map.get(key)
        if row is None:
            row = row_map[key] = {
                "project": e.project or "",
                "earner": e.earner,
                "by_month": {},
            }
        row["by_month"].setdefault(e.month_id, []).append(e)

    rows = []
    for r in sorted(row_map.values(), key=lambda r: (r["project"].lower(), r["earner"].name.lower())):
        cells = []
        for m in months:
            es = r["by_month"].get(m.id, [])
            cells.append({
                "month": m,
                "earnings": es,
                "first": es[0] if es else None,
                "count": len(es),
                "total": sum((x.amount for x in es), Decimal("0")),
            })
        r["cells"] = cells
        rows.append(r)
    return rows, months, orphans


@login_required
def earning_list(request):
    cell_param = request.GET.get("cell", "")
    edit_pk = None
    edit_form = None
    new_cell = None
    new_form = None

    if cell_param.isdigit():
        e = Earning.objects.filter(pk=int(cell_param)).select_related("month").first()
        if e and e.month_id and e.month.is_editable:
            edit_pk = e.pk
            edit_form = EarningCellForm(instance=e, form_id="form-cell-edit")
    elif cell_param == "new":
        earner_id = request.GET.get("earner", "")
        month_id = request.GET.get("month", "")
        project = request.GET.get("project", "")
        if earner_id.isdigit() and month_id.isdigit():
            month = Month.objects.filter(pk=int(month_id)).first()
            if month and month.is_editable and Person.objects.filter(pk=int(earner_id)).exists():
                new_cell = {
                    "project": project,
                    "earner_id": int(earner_id),
                    "month_id": int(month_id),
                }
                new_form = EarningCellForm(
                    initial={
                        "project": project,
                        "earner": int(earner_id),
                        "month": int(month_id),
                        "received_on": timezone.localdate(),
                    },
                    form_id="form-cell-new",
                )

    add_form = EarningForm(form_id="form-add-row")
    rows, months, orphans = _build_pivot()
    return render(
        request,
        "earnings/list.html",
        {
            "rows": rows,
            "months": months,
            "orphans": orphans,
            "edit_pk": edit_pk,
            "edit_form": edit_form,
            "new_cell": new_cell,
            "new_form": new_form,
            "add_form": add_form,
        },
    )


@require_POST
@login_required
def earning_create(request):
    """Shared endpoint for both the bottom add-row form and the in-cell
    new-earning form. On error we show a flash message and redirect back to
    the pivot — the form data is short enough that re-typing isn't painful."""
    form = EarningForm(request.POST)
    if form.is_valid():
        _save_form(form, user=request.user)
        messages.success(request, "Earning added.")
    else:
        details = "; ".join(f"{k}: {', '.join(v)}" for k, v in form.errors.items())
        messages.error(request, f"Could not add earning ({details}).")
    return redirect("earnings:list")


@require_POST
@login_required
def earning_update(request, pk: int):
    earning = get_object_or_404(Earning, pk=pk)
    if earning.month_id and not earning.month.is_editable:
        messages.error(request, "That month is closed; reopen it to edit earnings.")
        return redirect("earnings:list")
    form = EarningForm(request.POST, instance=earning)
    if form.is_valid():
        _save_form(form, user=request.user)
        messages.success(request, "Earning updated.")
    else:
        details = "; ".join(f"{k}: {', '.join(v)}" for k, v in form.errors.items())
        messages.error(request, f"Could not update earning ({details}).")
    return redirect("earnings:list")


@require_POST
@login_required
def earning_delete(request, pk: int):
    earning = get_object_or_404(Earning.objects.select_related("month"), pk=pk)
    if earning.month_id and not earning.month.is_editable:
        messages.error(request, "That month is closed; reopen it to delete earnings.")
        return redirect("earnings:list")
    label = f"{earning.earner} · {earning.amount}"
    month = earning.month
    earning.delete()
    settle_month_safe(month)
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
    if earning.month_id and not earning.month.is_editable:
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
