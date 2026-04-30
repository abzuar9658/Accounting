from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ExpenseForm
from .models import Expense


@login_required
def expense_list(request):
    """Single-screen CRUD view: list + inline add + per-row edit/delete.

    Toggling edit on a row is done with ``?edit=<pk>``; the matching row
    renders form fields tied (via the HTML ``form`` attribute) to an
    out-of-band form so we don't nest ``<form>`` tags inside the table.
    """
    expenses = list(
        Expense.objects.select_related("month", "category", "created_by")
    )
    edit_pk = None
    edit_form = None
    raw = request.GET.get("edit", "")
    if raw.isdigit():
        target = next((x for x in expenses if x.pk == int(raw)), None)
        if target and (not target.month_id or target.month.is_editable):
            edit_pk = target.pk
            edit_form = ExpenseForm(instance=target, form_id="form-expense-edit")

    add_form = ExpenseForm(form_id="form-expense-add")
    return render(
        request,
        "expenses/list.html",
        {
            "expenses": expenses,
            "edit_pk": edit_pk,
            "edit_form": edit_form,
            "add_form": add_form,
        },
    )


@require_POST
@login_required
def expense_create(request):
    form = ExpenseForm(request.POST, request.FILES)
    if form.is_valid():
        expense = form.save(commit=False)
        expense.created_by = request.user
        expense.save()
        messages.success(request, "Expense recorded.")
    else:
        details = "; ".join(f"{k}: {', '.join(v)}" for k, v in form.errors.items())
        messages.error(request, f"Could not add expense ({details}).")
    return redirect("expenses:list")


@require_POST
@login_required
def expense_update(request, pk: int):
    expense = get_object_or_404(Expense, pk=pk)
    if expense.month_id and not expense.month.is_editable:
        messages.error(request, "That month is closed; reopen it to edit expenses.")
        return redirect("expenses:list")
    form = ExpenseForm(request.POST, request.FILES, instance=expense)
    if form.is_valid():
        form.save()
        messages.success(request, "Expense updated.")
    else:
        details = "; ".join(f"{k}: {', '.join(v)}" for k, v in form.errors.items())
        messages.error(request, f"Could not update expense ({details}).")
    return redirect("expenses:list")


@require_POST
@login_required
def expense_delete(request, pk: int):
    expense = get_object_or_404(Expense.objects.select_related("month"), pk=pk)
    if expense.month_id and not expense.month.is_editable:
        messages.error(request, "That month is closed; reopen it to delete expenses.")
        return redirect("expenses:list")
    label = f"{expense.description or expense.amount}"
    expense.delete()
    messages.success(request, f"Deleted expense ({label}).")
    return redirect("expenses:list")


@login_required
def expense_edit(request, pk: int):
    """Backwards-compatible standalone edit page; primarily used to
    re-assign an orphaned row to a fresh month."""
    expense = get_object_or_404(Expense, pk=pk)
    if expense.month_id and not expense.month.is_editable:
        messages.error(request, "That month is closed; reopen it to edit expenses.")
        return redirect("expenses:list")
    if request.method == "POST":
        form = ExpenseForm(request.POST, request.FILES, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense updated.")
            return redirect("expenses:list")
    else:
        form = ExpenseForm(instance=expense)
    return render(request, "expenses/form.html", {"form": form, "expense": expense})
