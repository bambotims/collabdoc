from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.documents.models import Document


class DocUpdate(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="updates")
    seq = models.PositiveBigIntegerField()
    update_bytes = models.BinaryField()
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="doc_updates",
        null=True,
        blank=True,
    )
    size_bytes = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("document", "seq")
        indexes = [models.Index(fields=("document", "seq"), name="doc_update_seq_idx")]
        ordering = ("seq",)


class SnapshotKind(models.TextChoices):
    MANUAL = "manual", "Manual"
    SCHEDULED = "scheduled", "Scheduled"
    RESTORE = "restore", "Restore"


class DocSnapshot(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="snapshots")
    seq = models.PositiveBigIntegerField()
    snapshot_bytes = models.BinaryField()
    kind = models.CharField(max_length=16, choices=SnapshotKind.choices)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="doc_snapshots",
        null=True,
        blank=True,
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=("document", "seq"), name="doc_snapshot_seq_idx")]
        ordering = ("-seq",)
