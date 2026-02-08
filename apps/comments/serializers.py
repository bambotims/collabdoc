from __future__ import annotations

import base64

from rest_framework import serializers

from .models import CommentAnchor, CommentStatus, CommentThread


class CommentAnchorSerializer(serializers.ModelSerializer):
    start_rel_b64 = serializers.SerializerMethodField()
    end_rel_b64 = serializers.SerializerMethodField()

    class Meta:
        model = CommentAnchor
        fields = ("start_rel_b64", "end_rel_b64")

    def get_start_rel_b64(self, obj: CommentAnchor) -> str:
        return base64.b64encode(bytes(obj.start_rel_bytes)).decode("ascii")

    def get_end_rel_b64(self, obj: CommentAnchor) -> str:
        return base64.b64encode(bytes(obj.end_rel_bytes)).decode("ascii")


class CommentThreadSerializer(serializers.ModelSerializer):
    anchor = CommentAnchorSerializer(read_only=True)

    class Meta:
        model = CommentThread
        fields = (
            "id",
            "document_id",
            "author_id",
            "body",
            "status",
            "created_at",
            "updated_at",
            "resolved_at",
            "resolved_by_id",
            "anchor",
        )
        read_only_fields = (
            "id",
            "document_id",
            "author_id",
            "status",
            "created_at",
            "updated_at",
            "resolved_at",
            "resolved_by_id",
            "anchor",
        )


class CommentCreateSerializer(serializers.Serializer):
    body = serializers.CharField()
    start_rel_b64 = serializers.CharField()
    end_rel_b64 = serializers.CharField()

    def validate_start_rel_b64(self, value: str) -> str:
        base64.b64decode(value.encode("ascii"), validate=True)
        return value

    def validate_end_rel_b64(self, value: str) -> str:
        base64.b64decode(value.encode("ascii"), validate=True)
        return value

    def decode_anchor_bytes(self) -> tuple[bytes, bytes]:
        return (
            base64.b64decode(self.validated_data["start_rel_b64"].encode("ascii")),
            base64.b64decode(self.validated_data["end_rel_b64"].encode("ascii")),
        )


class CommentResolveSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=CommentStatus.choices)
