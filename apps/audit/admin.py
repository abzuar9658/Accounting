from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("happened_at", "actor", "action", "content_type", "object_repr")
    list_filter = ("action", "content_type")
    search_fields = ("object_repr", "notes")
    readonly_fields = (
        "happened_at", "actor", "action", "content_type",
        "object_id", "object_repr", "changed_fields", "notes",
    )

    def has_add_permission(self, request):  # noqa: D401
        return False

    def has_change_permission(self, request, obj=None):  # noqa: D401
        return False

    def has_delete_permission(self, request, obj=None):  # noqa: D401
        return False
