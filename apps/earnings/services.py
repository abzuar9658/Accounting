"""Allocation calculation and recomputation services."""
from decimal import Decimal

from django.db import transaction

from apps.common.money import quantize_amount
from apps.periods.models import Month, SplitRule

from .models import Allocation, Earning


@transaction.atomic
def generate_allocations(earning: Earning) -> list[Allocation]:
    """Wipe and regenerate the allocation rows for a single earning.

    The split rule for the earning's month is consulted; if no rule exists
    the earning has no allocations yet (the user is expected to configure
    the rule first).

    Rounding: each share is computed at storage precision (3 dp); any
    rounding residual is absorbed by the last row so the sum exactly
    matches the earning amount.
    """
    earning.allocations.all().delete()

    rule: SplitRule | None = getattr(earning.month, "split_rule", None)
    if rule is None:
        return []

    shares = list(rule.shares.all().order_by("-is_company", "person__name"))
    if not shares:
        return []

    rows: list[Allocation] = []
    running = Decimal("0")
    last_index = len(shares) - 1

    for idx, share in enumerate(shares):
        if idx == last_index:
            # Absorb the rounding residual on the last row.
            amount = quantize_amount(earning.amount - running)
        else:
            amount = quantize_amount(earning.amount * Decimal(share.percent) / Decimal(100))
            running += amount
        rows.append(
            Allocation(
                earning=earning,
                person=share.person,
                is_company=share.is_company,
                percent=share.percent,
                amount=amount,
            )
        )

    Allocation.objects.bulk_create(rows)
    return rows


def recompute_month_allocations(month: Month) -> int:
    """Regenerate allocations for every earning in the given month.

    Called after the month's split rule changes. Returns the number of
    earnings reprocessed.
    """
    count = 0
    for earning in month.earnings.all():
        generate_allocations(earning)
        count += 1
    return count
