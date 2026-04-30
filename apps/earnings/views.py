from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EarningForm
from .models import Earning
from .services import generate_allocations


@login_required
def earning_list(request):
    earnings = Earning.objects.select_related("month", "earner", "receiver_person")
    return render(request, "earnings/list.html", {"earnings": earnings})


@login_required
def earning_detail(request, pk: int):
    earning = get_object_or_404(
        Earning.objects.select_related("month", "earner", "receiver_person"),
        pk=pk,
    )
    return render(request, "earnings/detail.html", {"earning": earning})


@login_required
def earning_create(request):
    if request.method == "POST":
        form = EarningForm(request.POST)
        if form.is_valid():
            earning = form.save(commit=False)
            earning.created_by = request.user
            earning.save()
            generate_allocations(earning)
            messages.success(request, "Earning recorded.")
            return redirect("earnings:detail", pk=earning.pk)
    else:
        form = EarningForm()
    return render(request, "earnings/form.html", {"form": form})


@login_required
def earning_edit(request, pk: int):
    earning = get_object_or_404(Earning, pk=pk)
    if not earning.month.is_editable:
        messages.error(request, "That month is closed; reopen it to edit earnings.")
        return redirect("earnings:detail", pk=earning.pk)
    if request.method == "POST":
        form = EarningForm(request.POST, instance=earning)
        if form.is_valid():
            form.save()
            generate_allocations(earning)
            messages.success(request, "Earning updated.")
            return redirect("earnings:detail", pk=earning.pk)
    else:
        form = EarningForm(instance=earning)
    return render(request, "earnings/form.html", {"form": form, "earning": earning})
