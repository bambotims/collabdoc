from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from django.db import transaction
from django.db.models import Max

from pycrdt import Doc

from apps.collab.models import DocSnapshot, DocUpdate, SnapshotKind
from apps.documents.models import Document


@dataclass(frozen=True)
class LoadedState:
    snapshot_seq: int
    snapshot_bytes: bytes | None
    updates: list[bytes]


class PostgresYStore:
    """Postgres-backed CRDT persistence helper."""

    @staticmethod
    def get_latest_seq(document_id: str) -> int:
        latest = DocUpdate.objects.filter(document_id=document_id).aggregate(max_seq=Max("seq"))["max_seq"]
        return int(latest or 0)

    @staticmethod
    def append_update(*, document_id: str, update_bytes: bytes, actor_id: int | None = None) -> DocUpdate:
        with transaction.atomic():
            Document.objects.select_for_update().get(pk=document_id)
            last = (
                DocUpdate.objects.filter(document_id=document_id)
                .order_by("-seq", "-created_at")
                .values_list("seq", flat=True)
                .first()
            )
            next_seq = int(last or 0) + 1
            record = DocUpdate.objects.create(
                document_id=document_id,
                seq=next_seq,
                update_bytes=update_bytes,
                actor_id=actor_id,
                size_bytes=len(update_bytes),
            )
        return record

    @staticmethod
    def read_updates(*, document_id: str, from_seq: int | None = None) -> list[bytes]:
        queryset = DocUpdate.objects.filter(document_id=document_id)
        if from_seq is not None:
            queryset = queryset.filter(seq__gt=from_seq)
        return [bytes(value) for value in queryset.order_by("seq").values_list("update_bytes", flat=True)]

    @staticmethod
    def latest_snapshot(*, document_id: str) -> DocSnapshot | None:
        return DocSnapshot.objects.filter(document_id=document_id).order_by("-seq", "-created_at").first()

    @classmethod
    def load_state(cls, *, document_id: str) -> LoadedState:
        snapshot = cls.latest_snapshot(document_id=document_id)
        snapshot_seq = 0
        snapshot_bytes = None
        if snapshot is not None:
            snapshot_seq = snapshot.seq
            snapshot_bytes = bytes(snapshot.snapshot_bytes)

        updates = cls.read_updates(document_id=document_id, from_seq=snapshot_seq)
        return LoadedState(snapshot_seq=snapshot_seq, snapshot_bytes=snapshot_bytes, updates=updates)

    @classmethod
    def build_doc(cls, *, document_id: str) -> Doc:
        state = cls.load_state(document_id=document_id)
        doc = Doc()
        if state.snapshot_bytes:
            doc.apply_update(state.snapshot_bytes)
        for update in state.updates:
            doc.apply_update(update)
        return doc

    @staticmethod
    def create_snapshot(
        *,
        document_id: str,
        snapshot_bytes: bytes,
        kind: str,
        created_by_id: int | None,
        metadata: dict | None = None,
        seq: int | None = None,
    ) -> DocSnapshot:
        with transaction.atomic():
            Document.objects.select_for_update().get(pk=document_id)
            if seq is None:
                seq = PostgresYStore.get_latest_seq(document_id=document_id)
            return DocSnapshot.objects.create(
                document_id=document_id,
                seq=seq,
                snapshot_bytes=snapshot_bytes,
                kind=kind,
                created_by_id=created_by_id,
                metadata=metadata or {},
            )

    @classmethod
    def create_snapshot_from_current_state(
        cls,
        *,
        document_id: str,
        kind: str,
        created_by_id: int | None,
        metadata: dict | None = None,
    ) -> DocSnapshot:
        doc = cls.build_doc(document_id=document_id)
        snapshot_bytes = doc.get_update()
        seq = cls.get_latest_seq(document_id=document_id)
        return cls.create_snapshot(
            document_id=document_id,
            snapshot_bytes=snapshot_bytes,
            kind=kind,
            created_by_id=created_by_id,
            metadata=metadata,
            seq=seq,
        )

    @staticmethod
    def prune_updates_before(*, document_id: str, seq: int) -> int:
        deleted, _ = DocUpdate.objects.filter(document_id=document_id, seq__lt=seq).delete()
        return deleted


__all__ = ["LoadedState", "PostgresYStore", "SnapshotKind"]
