"""Append-only audit trail.

Every interesting write to a tracked model emits one :class:`AuditLog` row.
Rows are *generic* — they reference the originating object by content type
and id rather than via a hard FK, so we can audit any model without
plumbing a relation onto every table.
"""
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class AuditAction(models.TextChoices):
    CREATE = "create", "Created"
    UPDATE = "update", "Updated"
    DELETE = "delete", "Deleted"


class AuditLog(models.Model):
    happened_at = models.DateTimeField(auto_now_add=True, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="+",
    )
    action = models.CharField(max_length=10, choices=AuditAction.choices)

    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.PositiveBigIntegerField()
    target = GenericForeignKey("content_type", "object_id")

    object_repr = models.CharField(max_length=255)
    changed_fields = models.JSONField(default=dict, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("-happened_at", "-id")
        indexes = [
            models.Index(fields=("content_type", "object_id")),
            models.Index(fields=("action",)),
        ]

    def __str__(self) -> str:
        actor = self.actor.get_username() if self.actor else "system"
        return f"{actor} {self.get_action_display().lower()} {self.object_repr}"
