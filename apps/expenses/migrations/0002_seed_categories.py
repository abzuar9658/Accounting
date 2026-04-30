"""Seed the expense categories listed in the requirements doc."""
from django.db import migrations
from django.utils.text import slugify

DEFAULTS = [
    "Software subscription",
    "Hardware",
    "Internet",
    "Office rent",
    "Marketing",
    "Taxes",
    "Bank charges",
]


def seed(apps, schema_editor):
    ExpenseCategory = apps.get_model("expenses", "ExpenseCategory")
    for name in DEFAULTS:
        ExpenseCategory.objects.get_or_create(name=name, defaults={"slug": slugify(name)})


def unseed(apps, schema_editor):
    ExpenseCategory = apps.get_model("expenses", "ExpenseCategory")
    ExpenseCategory.objects.filter(name__in=DEFAULTS).delete()


class Migration(migrations.Migration):
    dependencies = [("expenses", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
