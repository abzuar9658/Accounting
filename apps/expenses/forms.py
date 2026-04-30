from django import forms

from apps.periods.models import Month, MonthStatus

from .models import Expense, ExpenseCategory


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ("month", "category", "happened_on", "amount", "description", "receipt")
        widgets = {
            "happened_on": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["month"].queryset = Month.objects.exclude(status=MonthStatus.CLOSED)
        self.fields["category"].queryset = ExpenseCategory.objects.filter(is_active=True)

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
