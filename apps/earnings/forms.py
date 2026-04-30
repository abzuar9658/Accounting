from django import forms

from apps.accounts.models import Person
from apps.periods.models import Month, MonthStatus

from .models import Earning, ReceiverKind


class EarningForm(forms.ModelForm):
    class Meta:
        model = Earning
        fields = (
            "month", "earner", "amount",
            "receiver_kind", "receiver_person",
            "received_on", "reference", "notes",
        )
        widgets = {
            "received_on": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Editable months only.
        self.fields["month"].queryset = Month.objects.exclude(status=MonthStatus.CLOSED)
        self.fields["earner"].queryset = Person.objects.filter(is_active=True)
        self.fields["receiver_person"].queryset = Person.objects.filter(is_active=True)
        self.fields["receiver_person"].required = False

    def clean(self):
        cleaned = super().clean()
        kind = cleaned.get("receiver_kind")
        person = cleaned.get("receiver_person")
        month = cleaned.get("month")
        if kind == ReceiverKind.COMPANY:
            cleaned["receiver_person"] = None
        elif kind == ReceiverKind.PERSON and person is None:
            self.add_error("receiver_person", "Required when the receiver is a person.")
        if month and not month.is_editable:
            raise forms.ValidationError("That month is closed.")
        return cleaned
