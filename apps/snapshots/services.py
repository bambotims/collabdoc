from __future__ import annotations

from apps.audit.services import record_audit_event
from apps.collab.models import DocSnapshot, SnapshotKind
from apps.collab.services import PostgresYStore


class SnapshotService:
    @staticmethod
    def create(*, document_id: str, actor_id: int | None, kind: str = SnapshotKind.MANUAL, metadata: dict | None = None) -> DocSnapshot:
        snapshot = PostgresYStore.create_snapshot_from_current_state(
            document_id=document_id,
            kind=kind,
            created_by_id=actor_id,
            metadata=metadata,
        )
        record_audit_event(
            document_id=document_id,
            actor_id=actor_id,
            event_type="snapshot.created",
            payload={"snapshot_id": snapshot.id, "seq": snapshot.seq, "kind": snapshot.kind},
        )
        return snapshot

    @staticmethod
    def restore(*, document_id: str, snapshot_id: int, actor_id: int | None) -> DocSnapshot:
        source = DocSnapshot.objects.filter(document_id=document_id, pk=snapshot_id).first()
        if source is None:
            raise DocSnapshot.DoesNotExist
        latest_seq = PostgresYStore.get_latest_seq(document_id=document_id)
        restored = PostgresYStore.create_snapshot(
            document_id=document_id,
            snapshot_bytes=bytes(source.snapshot_bytes),
            kind=SnapshotKind.RESTORE,
            created_by_id=actor_id,
            metadata={"source_snapshot_id": source.id},
            seq=latest_seq,
        )
        record_audit_event(
            document_id=document_id,
            actor_id=actor_id,
            event_type="snapshot.restored",
            payload={"source_snapshot_id": source.id, "restored_snapshot_id": restored.id, "seq": restored.seq},
        )
        return restored
