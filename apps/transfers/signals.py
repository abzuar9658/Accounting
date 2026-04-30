"""Keep transfer status and the company ledger in sync with payments."""
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.company.models import BalanceMovement, Company, MovementKind

from .models import PartyKind, Payment

SOURCE_APP = "transfers"
SOURCE_MODEL = "payment"


def _company_movement_for(payment: Payment) -> BalanceMovement | None:
    return BalanceMovement.objects.filter(
        source_app=SOURCE_APP, source_model=SOURCE_MODEL, source_id=payment.pk,
    ).first()


def _maybe_post_company_movement(payment: Payment) -> None:
    """Mirror a payment as a company cash movement when it touches the company."""
    transfer = payment.transfer
    company = Company.load()
    fields = dict(
        company=company,
        happened_on=payment.happened_on,
        source_app=SOURCE_APP,
        source_model=SOURCE_MODEL,
        source_id=payment.pk,
        created_by=payment.created_by,
    )
    code = transfer.month.code if transfer.month_id else "no month"
    if transfer.to_kind == PartyKind.COMPANY:
        fields.update(
            kind=MovementKind.RECEIPT,
            amount=payment.amount,
            description=f"Receipt from {transfer.from_label} ({code})"[:255],
        )
    elif transfer.from_kind == PartyKind.COMPANY:
        fields.update(
            kind=MovementKind.PAYOUT,
            amount=-payment.amount,
            description=f"Payout to {transfer.to_label} ({code})"[:255],
        )
    else:
        # Person-to-person payment; no company impact.
        return

    movement = _company_movement_for(payment)
    if movement is None:
        BalanceMovement.objects.create(**fields)
    else:
        for k, v in fields.items():
            setattr(movement, k, v)
        movement.save()


@receiver(post_save, sender=Payment)
def on_payment_saved(sender, instance: Payment, created, **kwargs):
    _maybe_post_company_movement(instance)
    transfer = instance.transfer
    transfer.recompute_status()
    transfer.save(update_fields=["status", "updated_at"])


@receiver(post_delete, sender=Payment)
def on_payment_deleted(sender, instance: Payment, **kwargs):
    BalanceMovement.objects.filter(
        source_app=SOURCE_APP, source_model=SOURCE_MODEL, source_id=instance.pk,
    ).delete()
    transfer = instance.transfer
    transfer.recompute_status()
    transfer.save(update_fields=["status", "updated_at"])
