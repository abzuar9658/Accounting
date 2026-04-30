"""Settlement engine.

For a given month we know:
  * how much each participant ACTUALLY received in their bank account
    (sum of earnings whose receiver is them); and
  * how much they OWN of the month's earnings (sum of allocations to them).

A positive ``imbalance = received - owns`` means the participant is holding
cash that doesn't belong to them; negative means cash is owed to them. The
mass balance always nets to zero.

We then greedily match positive holders against negative claimants,
producing the minimum set of aggregated transfers needed to make every
participant's position correct.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from django.db import transaction
from django.db.models import Sum

from apps.common.money import quantize_amount
from apps.earnings.models import Allocation, ReceiverKind
from apps.periods.models import Month

from .models import Payment, PartyKind, Transfer, TransferStatus

CENT = Decimal("0.001")


@dataclass(frozen=True)
class Party:
    kind: str
    person_id: int | None = None

    @classmethod
    def company(cls) -> "Party":
        return cls(kind=PartyKind.COMPANY)

    @classmethod
    def person(cls, person_id: int) -> "Party":
        return cls(kind=PartyKind.PERSON, person_id=person_id)


def _party_for_transfer_side(kind: str, person_id: int | None) -> Party:
    return Party.company() if kind == PartyKind.COMPANY else Party.person(person_id)


def _compute_balances(month: Month) -> dict[Party, Decimal]:
    """Return {party: imbalance} for the given month.

    ``imbalance > 0`` means the party is currently holding cash that ought to
    move elsewhere; ``imbalance < 0`` means cash is still owed to them.
    Payments already made against this month's transfers are netted in so
    re-settling never re-issues an obligation that has already been honoured.
    """
    balances: dict[Party, Decimal] = {}

    # received[party] - what landed in their account from earnings
    for e in month.earnings.all():
        party = Party.company() if e.receiver_kind == ReceiverKind.COMPANY else Party.person(e.receiver_person_id)
        balances[party] = balances.get(party, Decimal("0")) + e.amount

    # owns[party] - sum of allocations to that party in this month
    allocs = Allocation.objects.filter(earning__month=month)
    for row in allocs.values("person_id", "is_company").annotate(total=Sum("amount")):
        party = Party.company() if row["is_company"] else Party.person(row["person_id"])
        balances[party] = balances.get(party, Decimal("0")) - row["total"]

    # Net payments already settled against this month's transfers: each one is
    # cash that has effectively moved from sender to receiver, so subtract it
    # from the sender's surplus and add it to the receiver's surplus.
    payments = (
        Payment.objects
        .filter(transfer__month=month)
        .values(
            "transfer__from_kind", "transfer__from_person_id",
            "transfer__to_kind", "transfer__to_person_id",
        )
        .annotate(total=Sum("amount"))
    )
    for row in payments:
        sender = _party_for_transfer_side(row["transfer__from_kind"], row["transfer__from_person_id"])
        receiver = _party_for_transfer_side(row["transfer__to_kind"], row["transfer__to_person_id"])
        balances[sender] = balances.get(sender, Decimal("0")) - row["total"]
        balances[receiver] = balances.get(receiver, Decimal("0")) + row["total"]

    return balances


def _generate_transfers(balances: dict[Party, Decimal]) -> list[tuple[Party, Party, Decimal]]:
    """Greedy netting: match positive holders against negative claimants."""
    holders = sorted(((p, v) for p, v in balances.items() if v > CENT), key=lambda x: -x[1])
    claimants = sorted(((p, -v) for p, v in balances.items() if v < -CENT), key=lambda x: -x[1])

    pairs: list[tuple[Party, Party, Decimal]] = []
    i = j = 0
    while i < len(holders) and j < len(claimants):
        h_party, h_amt = holders[i]
        c_party, c_amt = claimants[j]
        amount = quantize_amount(min(h_amt, c_amt))
        if amount > 0:
            pairs.append((h_party, c_party, amount))
        h_amt -= amount
        c_amt -= amount
        if h_amt <= CENT:
            i += 1
        else:
            holders[i] = (h_party, h_amt)
        if c_amt <= CENT:
            j += 1
        else:
            claimants[j] = (c_party, c_amt)
    return pairs


def _to_transfer_kwargs(frm: Party, to: Party, amount: Decimal, month: Month) -> dict:
    return dict(
        month=month,
        from_kind=frm.kind,
        from_person_id=frm.person_id,
        to_kind=to.kind,
        to_person_id=to.person_id,
        amount=amount,
        auto_generated=True,
        status=TransferStatus.PENDING,
    )


@transaction.atomic
def settle_month(month: Month) -> list[Transfer]:
    """(Re)generate aggregated transfers for ``month``.

    Auto-generated transfers in PENDING status are wiped and rebuilt; any
    transfer that already has a recorded payment (PARTIAL/PAID) is left
    untouched so we don't lose evidence of work already done. Manual
    transfers are also untouched. The function is idempotent.
    """
    Transfer.objects.filter(month=month, auto_generated=True, status=TransferStatus.PENDING).delete()

    balances = _compute_balances(month)
    pairs = _generate_transfers(balances)

    created: list[Transfer] = []
    for frm, to, amount in pairs:
        created.append(Transfer.objects.create(**_to_transfer_kwargs(frm, to, amount, month)))
    return created


def settle_month_safe(month: Month | None) -> list[Transfer]:
    """Convenience wrapper for callers that want auto-settlement on writes.

    Skips the run when the month is missing (orphaned row) or no longer
    editable so callers don't have to special-case those branches at
    every site that records earnings, allocations or split-rule edits.
    """
    if month is None or not month.is_editable:
        return []
    return settle_month(month)


def pending_summary() -> Iterable[Transfer]:
    """All transfers that still owe money, across every month."""
    return (
        Transfer.objects.filter(status__in=[TransferStatus.PENDING, TransferStatus.PARTIAL])
        .select_related("month", "from_person", "to_person")
    )
