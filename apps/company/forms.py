from django import forms

from .models import BalanceMovement, Company, MovementKind


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = (
            "name",
            "opening_balance",
            "opening_balance_date",
            "bank_name",
            "bank_account_title",
            "bank_account_number",
            "bank_iban",
        )
        widgets = {
            "opening_balance_date": forms.DateInput(attrs={"type": "date"}),
        }


class ManualMovementForm(forms.ModelForm):
    """Form for the three movement kinds that admins enter by hand."""

    kind = forms.ChoiceField(
        choices=[
            (MovementKind.DEPOSIT, "Deposit"),
            (MovementKind.WITHDRAWAL, "Withdrawal"),
            (MovementKind.ADJUSTMENT, "Adjustment"),
        ]
    )

    class Meta:
        model = BalanceMovement
        fields = ("kind", "amount", "happened_on", "description")
        widgets = {
            "happened_on": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        kind = cleaned.get("kind")
        amount = cleaned.get("amount")
        if amount is None or kind is None:
            return cleaned
        # Withdrawals are stored as negative amounts; deposits as positive.
        # Adjustments accept either sign as the user enters them.
        if kind == MovementKind.WITHDRAWAL and amount > 0:
            cleaned["amount"] = -amount
        if kind == MovementKind.DEPOSIT and amount < 0:
            cleaned["amount"] = -amount
        return cleaned
