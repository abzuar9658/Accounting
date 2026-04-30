from django.contrib import admin

from .models import Month, SplitRule, SplitShare


class SplitShareInline(admin.TabularInline):
    model = SplitShare
    extra = 0
    autocomplete_fields = ("person",)


@admin.register(Month)
class MonthAdmin(admin.ModelAdmin):
    list_display = ("code", "label", "status", "closed_at")
    list_filter = ("status", "year")
    ordering = ("-year", "-month")


@admin.register(SplitRule)
class SplitRuleAdmin(admin.ModelAdmin):
    list_display = ("month", "total_percent")
    inlines = (SplitShareInline,)
