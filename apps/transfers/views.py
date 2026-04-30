from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.periods.models import Month

from .forms import PaymentForm
from .models import Payment, Transfer, TransferStatus
from .services import pending_summary, settle_month


def _is_admin(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name=settings.ROLE_ADMIN).exists()
    )


@login_required
def transfer_list(request):
    status = request.GET.get("status", "open")
    qs = Transfer.objects.select_related("month", "from_person", "to_person")
    if status == "open":
        qs = qs.filter(status__in=[TransferStatus.PENDING, TransferStatus.PARTIAL])
    elif status == "paid":
        qs = qs.filter(status=TransferStatus.PAID)
    elif status == "cancelled":
        qs = qs.filter(status=TransferStatus.CANCELLED)
    tabs = [("open", "Open"), ("paid", "Paid"), ("cancelled", "Cancelled"), ("all", "All")]
    return render(request, "transfers/list.html", {"transfers": qs, "status": status, "tabs": tabs})


@login_required
def transfer_detail(request, pk: int):
    transfer = get_object_or_404(
        Transfer.objects.select_related("month", "from_person", "to_person"), pk=pk
    )
    return render(request, "transfers/detail.html", {"transfer": transfer})


@login_required
def payment_create(request, pk: int):
    transfer = get_object_or_404(Transfer, pk=pk)
    if transfer.status in (TransferStatus.PAID, TransferStatus.CANCELLED):
        messages.error(request, "This transfer is already settled or cancelled.")
        return redirect("transfers:detail", pk=transfer.pk)

    if request.method == "POST":
        form = PaymentForm(request.POST, request.FILES, transfer=transfer)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.transfer = transfer
            payment.created_by = request.user
            payment.save()
            messages.success(request, "Payment recorded.")
            return redirect("transfers:detail", pk=transfer.pk)
    else:
        form = PaymentForm(transfer=transfer)
    return render(request, "transfers/payment_form.html", {"form": form, "transfer": transfer})


@require_POST
@login_required
def payment_quick(request, pk: int):
    """Record a payment in one click from the transfer detail page.

    Defaults to today's date and the full remaining amount; the user may
    override the amount via the inline input. Reference, proof and notes
    are intentionally omitted — the long-form ``payment_create`` view is
    still available when those are needed.
    """
    transfer = get_object_or_404(Transfer, pk=pk)
    if transfer.status in (TransferStatus.PAID, TransferStatus.CANCELLED):
        messages.error(request, "This transfer is already settled or cancelled.")
        return redirect("transfers:detail", pk=transfer.pk)

    raw = (request.POST.get("amount") or "").strip()
    remaining = transfer.amount_remaining
    try:
        amount = Decimal(raw) if raw else remaining
    except (InvalidOperation, TypeError):
        messages.error(request, "Enter a valid amount.")
        return redirect("transfers:detail", pk=transfer.pk)

    if amount <= 0:
        messages.error(request, "Amount must be positive.")
        return redirect("transfers:detail", pk=transfer.pk)
    if amount > remaining:
        messages.error(request, f"Cannot pay more than the remaining {remaining}.")
        return redirect("transfers:detail", pk=transfer.pk)

    Payment.objects.create(
        transfer=transfer,
        amount=amount,
        happened_on=timezone.localdate(),
        created_by=request.user,
    )
    messages.success(request, f"Recorded payment of {amount}.")
    return redirect("transfers:detail", pk=transfer.pk)


@login_required
@user_passes_test(_is_admin)
def settle_month_view(request, code: str):
    month = get_object_or_404(Month, year=int(code[:4]), month=int(code[5:7]))
    if not month.is_editable:
        messages.error(request, "Closed months cannot be re-settled.")
        return redirect("periods:month_detail", code=month.code)
    if request.method == "POST":
        created = settle_month(month)
        messages.success(request, f"Settlement complete: {len(created)} transfer(s) generated.")
        return redirect("periods:month_detail", code=month.code)
    return redirect("periods:month_detail", code=month.code)
