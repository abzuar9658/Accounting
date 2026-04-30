"""Keep the company's BalanceMovement ledger in sync with Expense rows."""
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.company.models import BalanceMovement, Company, MovementKind

from .models import Expense

SOURCE_APP = "expenses"
SOURCE_MODEL = "expense"


def _movement_for(expense: Expense):
    return BalanceMovement.objects.filter(
        source_app=SOURCE_APP, source_model=SOURCE_MODEL, source_id=expense.pk,
    ).first()


@receiver(post_save, sender=Expense)
def upsert_movement(sender, instance: Expense, created, **kwargs):
    """Create or update the matching negative cash movement."""
    company = Company.load()
    movement = _movement_for(instance)
    fields = dict(
        company=company,
        kind=MovementKind.EXPENSE,
        amount=-instance.amount,
        happened_on=instance.happened_on,
        description=f"{instance.category}: {instance.description}"[:255],
        source_app=SOURCE_APP,
        source_model=SOURCE_MODEL,
        source_id=instance.pk,
        created_by=instance.created_by,
    )
    if movement is None:
        BalanceMovement.objects.create(**fields)
    else:
        for k, v in fields.items():
            setattr(movement, k, v)
        movement.save()


@receiver(post_delete, sender=Expense)
def delete_movement(sender, instance: Expense, **kwargs):
    BalanceMovement.objects.filter(
        source_app=SOURCE_APP, source_model=SOURCE_MODEL, source_id=instance.pk,
    ).delete()
