"""Earnings and the per-participant allocations they generate."""
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.accounts.models import Person
from apps.periods.models import Month


class ReceiverKind(models.TextChoices):
    PERSON = "person", "Person"
    COMPANY = "company", "Company"


class Earning(models.Model):
    """A single payment received from a client/profile in a given month.

    The ``earner`` is who *generated* the income (e.g. the freelancer); the
    ``receiver_*`` fields record whose bank actually received the cash. They
    are usually the same person but they don't have to be.
    """

    month = models.ForeignKey(Month, on_delete=models.PROTECT, related_name="earnings")
    earner = models.ForeignKey(Person, on_delete=models.PROTECT, related_name="earnings")

    receiver_kind = models.CharField(max_length=10, choices=ReceiverKind.choices, default=ReceiverKind.PERSON)
    receiver_person = models.ForeignKey(
        Person,
        on_delete=models.PROTECT,
        related_name="received_earnings",
        null=True, blank=True,
    )

    amount = models.DecimalField(max_digits=14, decimal_places=3)
    received_on = models.DateField()
    reference = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-received_on", "-id")
        indexes = [models.Index(fields=("month", "earner"))]

    def __str__(self) -> str:
        return f"{self.earner} · {self.amount} ({self.month.code})"

    def clean(self):
        if self.receiver_kind == ReceiverKind.PERSON and self.receiver_person_id is None:
            raise ValidationError({"receiver_person": "Required when the receiver is a person."})
        if self.receiver_kind == ReceiverKind.COMPANY and self.receiver_person_id is not None:
            raise ValidationError({"receiver_person": "Must be empty when the receiver is the company."})
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({"amount": "Amount must be positive."})


class Allocation(models.Model):
    """The portion of a single earning owned by one split participant.

    Generated automatically from the month's ``SplitRule`` when an earning is
    saved. Stored explicitly (rather than recomputed on the fly) so each row
    keeps a snapshot of the percentage applied at that time.
    """

    earning = models.ForeignKey(Earning, on_delete=models.CASCADE, related_name="allocations")
    person = models.ForeignKey(Person, on_delete=models.PROTECT, null=True, blank=True, related_name="allocations")
    is_company = models.BooleanField(default=False)
    percent = models.PositiveSmallIntegerField()
    amount = models.DecimalField(max_digits=14, decimal_places=3, default=Decimal("0"))

    class Meta:
        ordering = ("-is_company", "person__name")
        constraints = [
            models.UniqueConstraint(fields=("earning", "person"), name="earnings_alloc_unique_person", condition=models.Q(person__isnull=False)),
            models.UniqueConstraint(fields=("earning",), name="earnings_alloc_unique_company", condition=models.Q(is_company=True)),
        ]

    @property
    def label(self) -> str:
        return "Company" if self.is_company else (self.person.name if self.person else "—")

    def __str__(self) -> str:
        return f"{self.label}: {self.amount} ({self.percent}%)"
