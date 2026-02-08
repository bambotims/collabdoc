from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model

from .models import AuditEvent


User = get_user_model()


def record_audit_event(*, document_id: str, actor_id: int | None, event_type: str, payload: dict[str, Any] | None = None) -> AuditEvent:
    return AuditEvent.objects.create(
        document_id=document_id,
        actor_id=actor_id,
        event_type=event_type,
        payload=payload or {},
    )
