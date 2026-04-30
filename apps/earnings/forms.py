from django import forms

from apps.accounts.models import Person
from apps.periods.models import Month, MonthStatus

from .models import Earning, ReceiverKind


class EarningForm(forms.ModelForm):
    """Minimal form: month is derived from ``received_on`` server-side and the
    receiver defaults to the earner. See ``earnings.views`` for that wiring."""

    project = forms.CharField(max_length=120, required=True)

    class Meta:
        model = Earning
        fields = ("earner", "amount", "project", "received_on")
        widgets = {
            "received_on": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["earner"].queryset = Person.objects.filter(is_active=True)
        # Compact widgets for the inline table-row form.
        cls = "block w-full rounded-md border-slate-300 text-sm shadow-sm focus:border-brand-500 focus:ring-brand-500"
        for name, field in self.fields.items():
            attrs = field.widget.attrs
            attrs["class"] = (attrs.get("class", "") + " " + cls).strip()
            if name == "amount":
                attrs["placeholder"] = "0.00"
                attrs["step"] = "0.01"
            elif name == "project":
                attrs["placeholder"] = "Project"

    def clean(self):
        cleaned = super().clean()
        received_on = cleaned.get("received_on")
        if received_on:
            existing = Month.objects.filter(year=received_on.year, month=received_on.month).first()
            if existing and existing.status == MonthStatus.CLOSED:
                raise forms.ValidationError(
                    f"{existing.label} is closed; reopen it before adding earnings to it."
                )
            self.instance.month = Month.get_or_create_for(received_on.year, received_on.month)
        # Default the receiver to the earner so the model's clean() doesn't
        # complain about the field that's been hidden from this form.
        earner = cleaned.get("earner")
        if earner is not None:
            self.instance.receiver_kind = ReceiverKind.PERSON
            self.instance.receiver_person = earner
        return cleaned

