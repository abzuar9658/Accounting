"""Shared money helpers.

Amounts are stored with three decimal places of precision (so percentage
splits like 33% don't accumulate rounding error) and displayed with two.
"""
from decimal import ROUND_HALF_UP, Decimal

#: Quantum used when *storing* monetary amounts.
AMOUNT_QUANTUM = Decimal("0.001")

#: Quantum used when *displaying* monetary amounts.
DISPLAY_QUANTUM = Decimal("0.01")


def quantize_amount(value: Decimal) -> Decimal:
    """Quantize a decimal to the storage precision."""
    return Decimal(value).quantize(AMOUNT_QUANTUM, rounding=ROUND_HALF_UP)


def quantize_display(value: Decimal) -> Decimal:
    """Quantize a decimal to the display precision."""
    return Decimal(value).quantize(DISPLAY_QUANTUM, rounding=ROUND_HALF_UP)
