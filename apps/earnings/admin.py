from django.contrib import admin

from .models import Allocation, Earning


class AllocationInline(admin.TabularInline):
    model = Allocation
    extra = 0
    readonly_fields = ("person", "is_company", "percent", "amount")
    can_delete = False


@admin.register(Earning)
class EarningAdmin(admin.ModelAdmin):
    list_display = ("received_on", "month", "earner", "amount", "receiver_kind", "reference")
    list_filter = ("month", "earner", "receiver_kind")
    search_fields = ("reference", "notes")
    inlines = (AllocationInline,)
