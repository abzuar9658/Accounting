"""Company expenses. Always paid from the company account."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from apps.periods.models import Month


class ExpenseCategory(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "Expense categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Expense(models.Model):
    """Money paid out of the company's account for an operating cost."""

    month = models.ForeignKey(Month, on_delete=models.PROTECT, related_name="expenses")
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name="expenses")
    happened_on = models.DateField()
    amount = models.DecimalField(max_digits=14, decimal_places=3)
    description = models.CharField(max_length=255)
    receipt = models.FileField(upload_to="receipts/%Y/%m/", blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-happened_on", "-id")
        indexes = [models.Index(fields=("month", "category"))]

    def __str__(self) -> str:
        return f"{self.category} · {self.amount} on {self.happened_on}"

    def clean(self):
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({"amount": "Amount must be positive."})
