from django import forms

from .models import Payment, Transfer


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ("amount", "happened_on", "reference", "proof", "notes")
        widgets = {
            "happened_on": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, transfer: Transfer | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._transfer = transfer
        if transfer is not None:
            self.fields["amount"].initial = transfer.amount_remaining

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount is None or amount <= 0:
            raise forms.ValidationError("Amount must be positive.")
        if self._transfer is not None and amount > self._transfer.amount_remaining:
            raise forms.ValidationError(
                f"Cannot pay more than the remaining {self._transfer.amount_remaining}."
            )
        return amount
