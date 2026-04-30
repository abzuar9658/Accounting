from django.contrib import admin

from .models import Payment, Transfer


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ("month", "from_label", "to_label", "amount", "status", "auto_generated")
    list_filter = ("status", "auto_generated", "month")
    search_fields = ("notes",)
    inlines = (PaymentInline,)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("happened_on", "transfer", "amount", "reference", "created_by")
    list_filter = ("happened_on",)
