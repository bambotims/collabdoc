from __future__ import annotations

from rest_framework import serializers

from apps.collab.models import DocSnapshot


class SnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocSnapshot
        fields = ("id", "document_id", "seq", "kind", "created_by_id", "metadata", "created_at")
        read_only_fields = fields
