from django import forms

from .models import Person


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = (
            "name",
            "user",
            "bank_name",
            "bank_account_title",
            "bank_account_number",
            "bank_iban",
            "is_active",
            "notes",
        )
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 2}),
        }
