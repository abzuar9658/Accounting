from django import forms
from django.forms import inlineformset_factory

from .models import Month, MonthStatus, SplitRule, SplitShare


class MonthForm(forms.ModelForm):
    class Meta:
        model = Month
        fields = ("year", "month", "status", "notes")
        widgets = {
            "status": forms.Select(),
        }


class _SplitShareForm(forms.ModelForm):
    """A row in the split-rule formset.

    The company row is identified by ``is_company`` being true; in that case
    the ``person`` field is hidden and ignored.
    """

    class Meta:
        model = SplitShare
        fields = ("person", "is_company", "percent")
        widgets = {
            "is_company": forms.HiddenInput(),
        }


class SplitShareFormSetBase(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        total = 0
        company_rows = 0
        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get("DELETE"):
                continue
            total += form.cleaned_data.get("percent") or 0
            if form.cleaned_data.get("is_company"):
                company_rows += 1
        if total != 100:
            raise forms.ValidationError(f"Split percentages must sum to 100 (currently {total}).")
        if company_rows != 1:
            raise forms.ValidationError("Exactly one company share is required (set its percent to 0 to skip).")


SplitShareFormSet = inlineformset_factory(
    SplitRule,
    SplitShare,
    form=_SplitShareForm,
    formset=SplitShareFormSetBase,
    extra=0,
    can_delete=True,
)


class NewMonthForm(forms.Form):
    """Quick form on the months index for creating a new month."""

    year = forms.IntegerField(min_value=2000, max_value=2100)
    month = forms.IntegerField(min_value=1, max_value=12)

    def clean(self):
        cleaned = super().clean()
        year, month = cleaned.get("year"), cleaned.get("month")
        if year and month and Month.objects.filter(year=year, month=month).exists():
            raise forms.ValidationError("That month already exists.")
        return cleaned
