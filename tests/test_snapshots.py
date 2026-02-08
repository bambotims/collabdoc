import pytest

from apps.collab.models import SnapshotKind
from apps.collab.services import PostgresYStore
from apps.documents.models import Document
from apps.snapshots.services import SnapshotService


@pytest.mark.django_db
def test_snapshot_restore_creates_restore_snapshot(user_factory):
    owner = user_factory("snapshot_owner")
    document = Document.objects.create(title="Snapshot Doc", owner=owner)

    source = PostgresYStore.create_snapshot(
        document_id=str(document.id),
        snapshot_bytes=b"state-v1",
        kind=SnapshotKind.MANUAL,
        created_by_id=owner.id,
        metadata={"name": "v1"},
        seq=0,
    )

    restored = SnapshotService.restore(document_id=str(document.id), snapshot_id=source.id, actor_id=owner.id)

    assert restored.kind == SnapshotKind.RESTORE
    assert bytes(restored.snapshot_bytes) == b"state-v1"
    assert restored.metadata["source_snapshot_id"] == source.id
