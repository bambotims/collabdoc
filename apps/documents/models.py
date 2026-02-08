from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class DocumentRole(models.TextChoices):
    OWNER = "owner", "Owner"
    EDITOR = "editor", "Editor"
    COMMENTER = "commenter", "Commenter"
    VIEWER = "viewer", "Viewer"


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_documents",
    )
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)

    def __str__(self) -> str:
        return f"{self.title} ({self.id})"


class DocumentMembership(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="document_memberships")
    role = models.CharField(max_length=16, choices=DocumentRole.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("document", "user")
        indexes = [models.Index(fields=("document", "user"), name="doc_member_lookup_idx")]

    def __str__(self) -> str:
        return f"{self.document_id}:{self.user_id}:{self.role}"


class InviteLink(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="invites")
    token_hash = models.CharField(max_length=128, unique=True)
    role = models.CharField(max_length=16, choices=DocumentRole.choices)
    expires_at = models.DateTimeField()
    max_uses = models.PositiveIntegerField(default=1)
    use_count = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_invites",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    @property
    def is_expired(self) -> bool:
        from django.utils import timezone

        return timezone.now() >= self.expires_at

    @property
    def is_exhausted(self) -> bool:
        return self.use_count >= self.max_uses
