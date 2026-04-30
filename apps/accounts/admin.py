from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Person, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "bank_name", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "bank_account_title", "bank_account_number", "bank_iban")
    autocomplete_fields = ("user",)
