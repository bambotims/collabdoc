from __future__ import annotations

from celery import shared_task

from apps.audit.services import record_audit_event
from apps.collab.models import SnapshotKind
from apps.collab.services import PostgresYStore
from apps.documents.models import Document


@shared_task
def scheduled_snapshot_task(update_threshold: int = 200) -> int:
    created = 0
    for document_id in Document.objects.values_list("id", flat=True):
        latest_seq = PostgresYStore.get_latest_seq(document_id=str(document_id))
        latest_snapshot = PostgresYStore.latest_snapshot(document_id=str(document_id))
        latest_snapshot_seq = latest_snapshot.seq if latest_snapshot else 0
        if latest_seq - latest_snapshot_seq < update_threshold:
            continue
        snapshot = PostgresYStore.create_snapshot_from_current_state(
            document_id=str(document_id),
            kind=SnapshotKind.SCHEDULED,
            created_by_id=None,
            metadata={"reason": "threshold", "threshold": update_threshold},
        )
        created += 1
        record_audit_event(
            document_id=str(document_id),
            actor_id=None,
            event_type="snapshot.scheduled",
            payload={"snapshot_id": snapshot.id, "seq": snapshot.seq},
        )
    return created


@shared_task
def compact_updates_task(document_id: str, retain_from_seq: int) -> int:
    return PostgresYStore.prune_updates_before(document_id=document_id, seq=retain_from_seq)
