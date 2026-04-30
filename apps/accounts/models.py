from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Project user. Kept thin so we can extend it later without surgery."""

    email = models.EmailField(unique=True)

    class Meta:
        ordering = ("username",)

    def __str__(self) -> str:
        return self.get_full_name() or self.username


class Person(models.Model):
    """A real person who participates in earnings and split rules.

    A person may or may not be linked to a login account (``user``).
    Bank details are kept here, not on the user, because they describe the
    real-world recipient of a transfer rather than an authentication record.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        related_name="person",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=120, unique=True)
    bank_name = models.CharField(max_length=120, blank=True)
    bank_account_title = models.CharField(max_length=120, blank=True)
    bank_account_number = models.CharField(max_length=64, blank=True)
    bank_iban = models.CharField("Bank IBAN", max_length=64, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "Person"
        verbose_name_plural = "People"

    def __str__(self) -> str:
        return self.name
