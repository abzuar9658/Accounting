from django import forms
from django.utils import timezone

from apps.accounts.models import Person
from apps.periods.models import Month, MonthStatus

from .models import Earning, ReceiverKind


class EarningForm(forms.ModelForm):
    """Minimal form: the user picks the month explicitly; the receiver
    defaults to the earner so the model's full clean is satisfied."""

    project = forms.CharField(max_length=120, required=True)

    class Meta:
        model = Earning
        fields = ("month", "earner", "amount", "project", "received_on")
        widgets = {
            "received_on": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["earner"].queryset = Person.objects.filter(is_active=True)
        self.fields["month"].queryset = Month.objects.exclude(status=MonthStatus.CLOSED)
        self.fields["month"].empty_label = "Pick month"
        # Default the month to the latest editable one and the date to today
        # so the inline-add row is one click away from being submittable.
        if not self.is_bound and self.instance.pk is None:
            if not self.initial.get("month"):
                latest = self.fields["month"].queryset.first()
                if latest:
                    self.initial["month"] = latest.pk
            if not self.initial.get("received_on"):
                self.initial["received_on"] = timezone.localdate()
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
        month = cleaned.get("month")
        if month and not month.is_editable:
            raise forms.ValidationError(
                f"{month.label} is closed; reopen it before adding earnings to it."
            )
        # Default the receiver to the earner so the model's clean() doesn't
        # complain about the field that's been hidden from this form.
        earner = cleaned.get("earner")
        if earner is not None:
            self.instance.receiver_kind = ReceiverKind.PERSON
            self.instance.receiver_person = earner
        return cleaned

