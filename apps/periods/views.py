from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.models import Person

from .forms import NewMonthForm, SplitShareFormSet
from .models import Month, SplitRule, SplitShare


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

    rule, created = SplitRule.objects.get_or_create(month=month)
    if created:
        # Pre-populate one row per active person + a single company row.
        for person in Person.objects.filter(is_active=True):
            SplitShare.objects.create(rule=rule, person=person, percent=0)
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
