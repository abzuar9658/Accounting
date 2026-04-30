from django import forms
from django.utils import timezone

from apps.periods.models import Month, MonthStatus

from .models import Expense, ExpenseCategory


class ExpenseForm(forms.ModelForm):
    """Inline expense form: ``category`` is omitted (left blank by default);
    the user picks the month explicitly and the receipt date defaults to
    today so a row is one click away from being submittable."""

    class Meta:
        model = Expense
        fields = ("month", "happened_on", "amount", "description", "receipt")
        widgets = {
            "happened_on": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, form_id: str | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._form_id = form_id
        self.fields["month"].queryset = Month.objects.exclude(status=MonthStatus.CLOSED)
        self.fields["month"].empty_label = "Pick month"
        # Sensible defaults for the inline-add row.
        if not self.is_bound and self.instance.pk is None:
            if not self.initial.get("month"):
                latest = self.fields["month"].queryset.first()
                if latest:
                    self.initial["month"] = latest.pk
            if not self.initial.get("happened_on"):
                self.initial["happened_on"] = timezone.localdate()
        cls = "block w-full rounded-md border-slate-300 text-sm shadow-sm focus:border-brand-500 focus:ring-brand-500"
        for name, field in self.fields.items():
            attrs = field.widget.attrs
            attrs["class"] = (attrs.get("class", "") + " " + cls).strip()
            if self._form_id:
                attrs["form"] = self._form_id
            if name == "amount":
                attrs["placeholder"] = "0.00"
                attrs["step"] = "0.01"
            elif name == "description":
                attrs["placeholder"] = "Description"

    def clean(self):
        cleaned = super().clean()
        month = cleaned.get("month")
        if month and not month.is_editable:
            raise forms.ValidationError("That month is closed.")
        return cleaned


class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExpenseCategory
        fields = ("name", "is_active")
