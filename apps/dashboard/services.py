"""Read-only aggregations for the dashboard and monthly report.

Everything in here is computed lazily from the existing app models — no
denormalised storage, so the numbers are always current.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from django.db.models import Sum

from apps.accounts.models import Person
from apps.company.models import Company
from apps.earnings.models import Allocation, ReceiverKind
from apps.periods.models import Month
from apps.transfers.models import Transfer, TransferStatus

ZERO = Decimal("0")


@dataclass
class PersonStanding:
    """One person's position in a single month."""
    person: Person
    received: Decimal
    owns: Decimal
    paid_out: Decimal
    paid_in: Decimal

    @property
    def imbalance(self) -> Decimal:
        """Positive: still holding others' money. Negative: still owed money."""
        return self.received - self.owns - self.paid_out + self.paid_in


@dataclass
class CompanyStanding:
    received: Decimal
    owns: Decimal
    paid_in: Decimal
    paid_out: Decimal

    @property
    def imbalance(self) -> Decimal:
        return self.received - self.owns - self.paid_out + self.paid_in


def _current_month() -> Optional[Month]:
    return Month.objects.order_by("-year", "-month").first()


def _payments_into(month: Month, *, to_company: bool = False, person: Person | None = None) -> Decimal:
    qs = month.transfers.filter(payments__isnull=False)
    if to_company:
        qs = qs.filter(to_kind="company")
    elif person is not None:
        qs = qs.filter(to_kind="person", to_person=person)
    return qs.aggregate(t=Sum("payments__amount"))["t"] or ZERO


def _payments_out_of(month: Month, *, from_company: bool = False, person: Person | None = None) -> Decimal:
    qs = month.transfers.filter(payments__isnull=False)
    if from_company:
        qs = qs.filter(from_kind="company")
    elif person is not None:
        qs = qs.filter(from_kind="person", from_person=person)
    return qs.aggregate(t=Sum("payments__amount"))["t"] or ZERO


def person_standings(month: Month) -> list[PersonStanding]:
    standings = []
    for person in Person.objects.filter(is_active=True).order_by("name"):
        received = (
            month.earnings.filter(receiver_kind=ReceiverKind.PERSON, receiver_person=person)
            .aggregate(t=Sum("amount"))["t"] or ZERO
        )
        owns = (
            Allocation.objects.filter(earning__month=month, person=person)
            .aggregate(t=Sum("amount"))["t"] or ZERO
        )
        standings.append(PersonStanding(
            person=person,
            received=received,
            owns=owns,
            paid_out=_payments_out_of(month, person=person),
            paid_in=_payments_into(month, person=person),
        ))
    return standings


def company_standing(month: Month) -> CompanyStanding:
    received = (
        month.earnings.filter(receiver_kind=ReceiverKind.COMPANY)
        .aggregate(t=Sum("amount"))["t"] or ZERO
    )
    owns = (
        Allocation.objects.filter(earning__month=month, is_company=True)
        .aggregate(t=Sum("amount"))["t"] or ZERO
    )
    return CompanyStanding(
        received=received,
        owns=owns,
        paid_in=_payments_into(month, to_company=True),
        paid_out=_payments_out_of(month, from_company=True),
    )


def dashboard_context() -> dict:
    company = Company.load()
    month = _current_month()

    pending = Transfer.objects.filter(
        status__in=[TransferStatus.PENDING, TransferStatus.PARTIAL]
    )
    pending_total = sum((t.amount_remaining for t in pending), ZERO)

    ctx = {
        "company": company,
        "company_balance": company.current_balance,
        "month": month,
        "pending_count": pending.count(),
        "pending_total": pending_total,
        "pending_transfers": pending.select_related("month", "from_person", "to_person")[:10],
    }

    if month is None:
        return ctx

    earnings_total = month.earnings.aggregate(t=Sum("amount"))["t"] or ZERO
    expenses_total = month.expenses.aggregate(t=Sum("amount"))["t"] or ZERO
    company_share = (
        Allocation.objects.filter(earning__month=month, is_company=True)
        .aggregate(t=Sum("amount"))["t"] or ZERO
    )

    ctx.update(
        earnings_total=earnings_total,
        expenses_total=expenses_total,
        company_share=company_share,
        company_net=company_share - expenses_total,
        person_standings=person_standings(month),
        company_standing=company_standing(month),
        recent_earnings=month.earnings.select_related("earner", "receiver_person")[:5],
        recent_expenses=month.expenses.select_related("category")[:5],
    )
    return ctx


def monthly_report(month: Month) -> dict:
    """Detailed per-month breakdown matching the template in the spec."""
    earnings = list(month.earnings.select_related("earner", "receiver_person"))
    rule = getattr(month, "split_rule", None)
    expenses = list(month.expenses.select_related("category"))
    transfers = list(month.transfers.select_related("from_person", "to_person"))

    earnings_by_earner: dict[str, Decimal] = {}
    for e in earnings:
        earnings_by_earner[e.earner.name] = earnings_by_earner.get(e.earner.name, ZERO) + e.amount

    expenses_by_category: dict[str, Decimal] = {}
    for x in expenses:
        expenses_by_category[x.category.name] = expenses_by_category.get(x.category.name, ZERO) + x.amount

    earnings_total = sum(earnings_by_earner.values(), ZERO)
    expenses_total = sum(expenses_by_category.values(), ZERO)

    standings = person_standings(month)
    company = company_standing(month)
    company_net = company.owns - expenses_total

    return {
        "month": month,
        "rule": rule,
        "earnings": earnings,
        "earnings_by_earner": earnings_by_earner,
        "earnings_total": earnings_total,
        "expenses": expenses,
        "expenses_by_category": expenses_by_category,
        "expenses_total": expenses_total,
        "transfers": transfers,
        "person_standings": standings,
        "company_standing": company,
        "company_net": company_net,
    }
