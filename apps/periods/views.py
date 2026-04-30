from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.models import Person

from .forms import NewMonthForm, SplitShareFormSet
from .models import Month, MonthStatus, SplitRule, SplitShare


def _is_admin(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name=settings.ROLE_ADMIN).exists()
    )


@login_required
def month_list(request):
    months = Month.objects.all().select_related("split_rule")
    new_form = NewMonthForm()
    if request.method == "POST" and _is_admin(request.user):
        new_form = NewMonthForm(request.POST)
        if new_form.is_valid():
            m = Month.objects.create(**new_form.cleaned_data)
            messages.success(request, f"Created {m}.")
            return redirect("periods:month_detail", code=m.code)
    return render(request, "periods/month_list.html", {"months": months, "form": new_form})


@login_required
def month_detail(request, code: str):
    month = get_object_or_404(Month, year=int(code[:4]), month=int(code[5:7]))
    rule = getattr(month, "split_rule", None)
    transfers = month.transfers.select_related("from_person", "to_person")
    return render(
        request,
        "periods/month_detail.html",
        {"month": month, "rule": rule, "transfers": transfers},
    )


@login_required
@user_passes_test(_is_admin)
def split_edit(request, code: str):
    month = get_object_or_404(Month, year=int(code[:4]), month=int(code[5:7]))
    if not month.is_editable:
        messages.error(request, "This month is closed; reopen it to edit the split rule.")
        return redirect("periods:month_detail", code=month.code)

    rule, _ = SplitRule.objects.get_or_create(month=month)
    # Make sure every active person and the company have a row, so that newly
    # added people show up here without manual intervention.
    existing_person_ids = set(rule.shares.exclude(person=None).values_list("person_id", flat=True))
    for person in Person.objects.filter(is_active=True).exclude(id__in=existing_person_ids):
        SplitShare.objects.create(rule=rule, person=person, percent=0)
    if not rule.shares.filter(is_company=True).exists():
        SplitShare.objects.create(rule=rule, is_company=True, percent=0)

    if request.method == "POST":
        formset = SplitShareFormSet(request.POST, instance=rule)
        if formset.is_valid():
            formset.save()
            # Recompute allocations for any earnings already in this month.
            from apps.earnings.services import recompute_month_allocations
            recompute_month_allocations(month)
            messages.success(request, "Split rule saved.")
            return redirect("periods:month_detail", code=month.code)
    else:
        formset = SplitShareFormSet(instance=rule)

    return render(
        request,
        "periods/split_form.html",
        {"month": month, "rule": rule, "formset": formset},
    )


_VALID_TRANSITIONS = {
    MonthStatus.OPEN: {MonthStatus.REVIEW, MonthStatus.CLOSED},
    MonthStatus.REVIEW: {MonthStatus.OPEN, MonthStatus.CLOSED},
    MonthStatus.CLOSED: {MonthStatus.OPEN},
}


@require_POST
@login_required
@user_passes_test(_is_admin)
def month_delete(request, code: str):
    """Delete a month. Earnings, expenses and transfers attached to it are
    detached (their ``month`` becomes null) rather than removed; the month's
    SplitRule is cascaded out as part of the delete."""
    month = get_object_or_404(Month, year=int(code[:4]), month=int(code[5:7]))
    label = month.label
    month.delete()
    messages.success(request, f"Deleted {label}; attached entries are now orphaned.")
    return redirect("periods:month_list")


@require_POST
@login_required
@user_passes_test(_is_admin)
def month_transition(request, code: str, target: str):
    month = get_object_or_404(Month, year=int(code[:4]), month=int(code[5:7]))
    new_status = MonthStatus(target) if target in MonthStatus.values else None
    if new_status is None or new_status not in _VALID_TRANSITIONS.get(month.status, set()):
        messages.error(request, f"Cannot move month from {month.get_status_display()} to {target}.")
        return redirect("periods:month_detail", code=month.code)

    month.status = new_status
    if new_status == MonthStatus.CLOSED:
        month.closed_at = timezone.now()
        month.closed_by = request.user
    else:
        month.closed_at = None
        month.closed_by = None
    month.save(update_fields=("status", "closed_at", "closed_by", "updated_at"))
    messages.success(request, f"{month.label} is now {month.get_status_display()}.")
    return redirect("periods:month_detail", code=month.code)
