"""Calendar months and the split rule that governs each one."""
from __future__ import annotations

import calendar
from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum

from apps.accounts.models import Person


class MonthStatus(models.TextChoices):
    OPEN = "open", "Open"
    REVIEW = "review", "Under review"
    CLOSED = "closed", "Closed"


class Month(models.Model):
    """A calendar month with a status lifecycle.

    Edits to earnings, expenses and split rules are allowed while the month is
    OPEN or REVIEW; CLOSED months are read-only until an admin reopens them.
    """

    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=10, choices=MonthStatus.choices, default=MonthStatus.OPEN)
    notes = models.TextField(blank=True)

    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-year", "-month")
        constraints = [
            models.UniqueConstraint(fields=("year", "month"), name="periods_month_unique"),
            models.CheckConstraint(check=models.Q(month__gte=1, month__lte=12), name="periods_month_range"),
        ]

    def __str__(self) -> str:
        return self.label

    @property
    def label(self) -> str:
        return f"{calendar.month_name[self.month]} {self.year}"

    @property
    def code(self) -> str:
        """ISO-style YYYY-MM identifier used in URLs."""
        return f"{self.year:04d}-{self.month:02d}"

    @property
    def first_day(self) -> date:
        return date(self.year, self.month, 1)

    @property
    def last_day(self) -> date:
        return date(self.year, self.month, calendar.monthrange(self.year, self.month)[1])

    @property
    def is_editable(self) -> bool:
        return self.status != MonthStatus.CLOSED

    @classmethod
    def get_or_create_for(cls, year: int, month: int) -> "Month":
        obj, _ = cls.objects.get_or_create(year=year, month=month)
        return obj

    @classmethod
    def from_code(cls, code: str) -> "Month":
        year_str, month_str = code.split("-", 1)
        return cls.objects.get(year=int(year_str), month=int(month_str))


class SplitRule(models.Model):
    """The split rule attached to a month.

    A rule owns one or more ``SplitShare`` rows whose ``percent`` values must
    sum to exactly 100. Every rule must include exactly one share that
    represents the Company; other shares each point at a Person.
    """

    month = models.OneToOneField(Month, on_delete=models.CASCADE, related_name="split_rule")
    notes = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Split for {self.month}"

    @property
    def total_percent(self) -> int:
        return self.shares.aggregate(t=Sum("percent"))["t"] or 0

    def clean(self):
        if self.pk and self.total_percent != 100:
            raise ValidationError("Split shares must sum to exactly 100%.")

    def participants_label(self) -> str:
        bits = []
        for s in self.shares.select_related("person"):
            bits.append(f"{s.label}: {s.percent}%")
        return " · ".join(bits)


class SplitShare(models.Model):
    """One participant's percentage within a ``SplitRule``."""

    rule = models.ForeignKey(SplitRule, on_delete=models.CASCADE, related_name="shares")
    person = models.ForeignKey(Person, on_delete=models.PROTECT, null=True, blank=True, related_name="split_shares")
    is_company = models.BooleanField(default=False)
    percent = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ("-is_company", "person__name")
        constraints = [
            models.CheckConstraint(check=models.Q(percent__gte=0, percent__lte=100), name="periods_share_percent_range"),
            models.UniqueConstraint(fields=("rule", "person"), name="periods_share_unique_person", condition=models.Q(person__isnull=False)),
            models.UniqueConstraint(fields=("rule",), name="periods_share_unique_company", condition=models.Q(is_company=True)),
        ]

    def clean(self):
        if self.is_company and self.person_id is not None:
            raise ValidationError("A company share cannot also point at a person.")
        if not self.is_company and self.person_id is None:
            raise ValidationError("A person must be selected for a non-company share.")

    @property
    def label(self) -> str:
        return "Company" if self.is_company else (self.person.name if self.person else "—")

    def __str__(self) -> str:
        return f"{self.label}: {self.percent}%"
