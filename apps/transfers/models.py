"""Transfers (payable/receivable) and the payments that settle them."""
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum

from apps.accounts.models import Person
from apps.periods.models import Month


class PartyKind(models.TextChoices):
    PERSON = "person", "Person"
    COMPANY = "company", "Company"


class TransferStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PARTIAL = "partial", "Partial"
    PAID = "paid", "Paid"
    CANCELLED = "cancelled", "Cancelled"


class Transfer(models.Model):
    """An obligation to move money from one party to another.

    A transfer is *aggregated*: the settlement engine produces one Transfer
    per (from, to) pair per month rather than one per allocation. Status is
    derived from the attached :class:`Payment` rows but stored for fast
    filtering by the dashboard.

    Pending or partial transfers from past months simply remain in this table,
    which is how unsettled balances "carry forward" — they keep showing up in
    the dashboard until they are fully paid or cancelled.
    """

    month = models.ForeignKey(Month, on_delete=models.PROTECT, related_name="transfers")

    from_kind = models.CharField(max_length=10, choices=PartyKind.choices)
    from_person = models.ForeignKey(Person, on_delete=models.PROTECT, null=True, blank=True, related_name="outgoing_transfers")

    to_kind = models.CharField(max_length=10, choices=PartyKind.choices)
    to_person = models.ForeignKey(Person, on_delete=models.PROTECT, null=True, blank=True, related_name="incoming_transfers")

    amount = models.DecimalField(max_digits=14, decimal_places=3)
    status = models.CharField(max_length=12, choices=TransferStatus.choices, default=TransferStatus.PENDING)

    auto_generated = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-month__year", "-month__month", "status", "id")
        indexes = [
            models.Index(fields=("status",)),
            models.Index(fields=("month", "status")),
        ]

    def __str__(self) -> str:
        return f"{self.from_label} → {self.to_label}: {self.amount} ({self.month.code})"

    def clean(self):
        if self.from_kind == PartyKind.PERSON and self.from_person_id is None:
            raise ValidationError({"from_person": "Required when sender is a person."})
        if self.to_kind == PartyKind.PERSON and self.to_person_id is None:
            raise ValidationError({"to_person": "Required when receiver is a person."})
        if self.from_kind == self.to_kind and self.from_person_id == self.to_person_id:
            raise ValidationError("Sender and receiver cannot be the same party.")
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({"amount": "Amount must be positive."})

    @property
    def from_label(self) -> str:
        return "Company" if self.from_kind == PartyKind.COMPANY else (self.from_person.name if self.from_person else "—")

    @property
    def to_label(self) -> str:
        return "Company" if self.to_kind == PartyKind.COMPANY else (self.to_person.name if self.to_person else "—")

    @property
    def amount_paid(self) -> Decimal:
        return self.payments.aggregate(t=Sum("amount"))["t"] or Decimal("0")

    @property
    def amount_remaining(self) -> Decimal:
        return max(self.amount - self.amount_paid, Decimal("0"))

    def recompute_status(self) -> None:
        if self.status == TransferStatus.CANCELLED:
            return
        paid = self.amount_paid
        if paid <= 0:
            self.status = TransferStatus.PENDING
        elif paid < self.amount:
            self.status = TransferStatus.PARTIAL
        else:
            self.status = TransferStatus.PAID


class Payment(models.Model):
    """A single (possibly partial) payment recorded against a Transfer."""

    transfer = models.ForeignKey(Transfer, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=14, decimal_places=3)
    happened_on = models.DateField()
    reference = models.CharField(max_length=120, blank=True)
    proof = models.FileField(upload_to="proofs/%Y/%m/", blank=True, null=True)
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-happened_on", "-id")

    def __str__(self) -> str:
        return f"Payment {self.amount} on {self.happened_on}"

    def clean(self):
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({"amount": "Amount must be positive."})
