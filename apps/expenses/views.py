from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ExpenseForm
from .models import Expense


@login_required
def expense_list(request):
    expenses = Expense.objects.select_related("month", "category", "created_by")
    return render(request, "expenses/list.html", {"expenses": expenses})


@login_required
def expense_create(request):
    if request.method == "POST":
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.created_by = request.user
            expense.save()
            messages.success(request, "Expense recorded.")
            return redirect("expenses:list")
    else:
        form = ExpenseForm()
    return render(request, "expenses/form.html", {"form": form})


@login_required
def expense_edit(request, pk: int):
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
