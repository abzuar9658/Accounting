"""Template filters for money rendering."""
from decimal import Decimal, InvalidOperation

from django import template

from apps.common.money import quantize_display

register = template.Library()


@register.filter(name="pkr")
def pkr(value) -> str:
    """Render a decimal amount as PKR with grouped thousands and 2 dp."""
    if value is None or value == "":
        return "—"
    try:
        amount = quantize_display(Decimal(value))
    except (InvalidOperation, TypeError, ValueError):
        return str(value)
    sign = "-" if amount < 0 else ""
    integer, _, fraction = f"{abs(amount):.2f}".partition(".")
    grouped = f"{int(integer):,}"
    return f"{sign}PKR {grouped}.{fraction}"


@register.filter(name="amount")
def amount(value) -> str:
    """Render a decimal amount with grouped thousands and 2 dp (no currency)."""
    if value is None or value == "":
        return "—"
    try:
        a = quantize_display(Decimal(value))
    except (InvalidOperation, TypeError, ValueError):
        return str(value)
    sign = "-" if a < 0 else ""
    integer, _, fraction = f"{abs(a):.2f}".partition(".")
    return f"{sign}{int(integer):,}.{fraction}"
