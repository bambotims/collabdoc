from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.documents.models import Document


class AuditEvent(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="audit_events")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    event_type = models.CharField(max_length=64)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=("document", "created_at"), name="audit_doc_time_idx")]
        ordering = ("-created_at",)
