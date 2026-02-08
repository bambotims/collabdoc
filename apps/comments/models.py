from __future__ import annotations

from django.conf import settings
from django.db import models

from apps.documents.models import Document


class CommentStatus(models.TextChoices):
    OPEN = "open", "Open"
    RESOLVED = "resolved", "Resolved"


class CommentThread(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="comment_threads")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="authored_comment_threads",
    )
    body = models.TextField()
    status = models.CharField(max_length=16, choices=CommentStatus.choices, default=CommentStatus.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="resolved_comment_threads",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("-created_at",)


class CommentAnchor(models.Model):
    thread = models.OneToOneField(CommentThread, on_delete=models.CASCADE, related_name="anchor")
    start_rel_bytes = models.BinaryField()
    end_rel_bytes = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)
