from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Document, DocumentMembership, DocumentRole, InviteLink

User = get_user_model()


class DocumentSerializer(serializers.ModelSerializer):
    my_role = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            "id",
            "title",
            "owner_id",
            "is_archived",
            "created_at",
            "updated_at",
            "my_role",
        )
        read_only_fields = ("id", "owner_id", "created_at", "updated_at", "my_role")

    def get_my_role(self, obj: Document) -> str | None:
        role = self.context.get("my_role")
        if role:
            return role
        user = self.context["request"].user
        if obj.owner_id == user.id:
            return DocumentRole.OWNER
        membership = obj.memberships.filter(user=user).first()
        return membership.role if membership else None


class DocumentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ("title",)


class DocumentMembershipSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(source="user", queryset=User.objects.all())
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = DocumentMembership
        fields = ("id", "user_id", "username", "role", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at", "username")


class InviteCreateSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=DocumentRole.choices)
    expires_at = serializers.DateTimeField()
    max_uses = serializers.IntegerField(min_value=1, default=1)


class InviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = InviteLink
        fields = (
            "id",
            "role",
            "expires_at",
            "max_uses",
            "use_count",
            "created_by_id",
            "created_at",
        )


class InviteIssuedSerializer(InviteSerializer):
    token = serializers.CharField()


class CollabTokenSerializer(serializers.Serializer):
    token = serializers.CharField()
    expires_at = serializers.DateTimeField()
    role = serializers.ChoiceField(choices=DocumentRole.choices)
