from __future__ import annotations

import hashlib
import os
import secrets
import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Iterable

import jwt
from django.conf import settings
from django.db.models import Q
from django.http import Http404
from django.utils import timezone

from .models import Document, DocumentMembership, DocumentRole, InviteLink

ROLE_RANK = {
    DocumentRole.VIEWER: 1,
    DocumentRole.COMMENTER: 2,
    DocumentRole.EDITOR: 3,
    DocumentRole.OWNER: 4,
}


class CollabTokenError(Exception):
    """Raised when a collab token is invalid."""


@dataclass(frozen=True)
class TokenClaims:
    sub: str
    user_id: int
    doc_id: str
    role: str
    exp: int
    jti: str


class ACLService:
    @staticmethod
    def visible_documents(user) -> Iterable[Document]:
        return Document.objects.filter(Q(owner=user) | Q(memberships__user=user)).distinct()

    @staticmethod
    def role_for_document(user, document: Document) -> str | None:
        if user.is_anonymous:
            return None
        if document.owner_id == user.id:
            return DocumentRole.OWNER
        membership = DocumentMembership.objects.filter(document=document, user=user).first()
        return membership.role if membership else None

    @staticmethod
    def role_meets(actual_role: str | None, required_role: str) -> bool:
        if actual_role is None:
            return False
        return ROLE_RANK[actual_role] >= ROLE_RANK[required_role]

    @classmethod
    def check(cls, *, user, doc_id: str, required_role: str = DocumentRole.VIEWER) -> bool:
        document = Document.objects.filter(pk=doc_id).first()
        if not document:
            return False
        role = cls.role_for_document(user, document)
        return cls.role_meets(role, required_role)

    @classmethod
    def get_document_or_404(cls, *, user, doc_id: str, required_role: str = DocumentRole.VIEWER) -> tuple[Document, str]:
        document = Document.objects.filter(pk=doc_id).first()
        if not document:
            raise Http404("Document not found")
        role = cls.role_for_document(user, document)
        if not cls.role_meets(role, required_role):
            raise Http404("Document not found")
        return document, role


class CollabTokenService:
    TOKEN_TTL_SECONDS = int(os.getenv("COLLAB_TOKEN_TTL_SECONDS", "600"))

    @classmethod
    def mint(cls, *, user_id: int, doc_id: str, role: str) -> tuple[str, timezone.datetime]:
        now = timezone.now()
        expires_at = now + timedelta(seconds=cls.TOKEN_TTL_SECONDS)
        claims = {
            "sub": str(user_id),
            "user_id": user_id,
            "doc_id": str(doc_id),
            "role": role,
            "exp": int(expires_at.timestamp()),
            "jti": uuid.uuid4().hex,
        }
        token = jwt.encode(claims, settings.SECRET_KEY, algorithm="HS256")
        return token, expires_at

    @classmethod
    def verify(cls, token: str, doc_id: str) -> TokenClaims:
        try:
            claims = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.PyJWTError as exc:
            raise CollabTokenError("Invalid collab token") from exc

        if str(claims.get("doc_id")) != str(doc_id):
            raise CollabTokenError("Token doc mismatch")

        role = claims.get("role")
        if role not in ROLE_RANK:
            raise CollabTokenError("Invalid role claim")

        return TokenClaims(
            sub=str(claims["sub"]),
            user_id=int(claims["user_id"]),
            doc_id=str(claims["doc_id"]),
            role=role,
            exp=int(claims["exp"]),
            jti=str(claims["jti"]),
        )


class InviteService:
    @staticmethod
    def create_invite(
        *,
        document: Document,
        role: str,
        expires_at,
        max_uses: int,
        created_by,
    ) -> tuple[InviteLink, str]:
        raw_token = secrets.token_urlsafe(24)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        invite = InviteLink.objects.create(
            document=document,
            role=role,
            expires_at=expires_at,
            max_uses=max_uses,
            created_by=created_by,
            token_hash=token_hash,
        )
        return invite, raw_token

    @staticmethod
    def consume_invite(*, raw_token: str, user) -> DocumentMembership:
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        invite = InviteLink.objects.filter(token_hash=token_hash).first()
        if invite is None or invite.is_expired or invite.is_exhausted:
            raise Http404("Invite not found")

        invite.use_count += 1
        invite.save(update_fields=["use_count"])

        membership, _ = DocumentMembership.objects.update_or_create(
            document=invite.document,
            user=user,
            defaults={"role": invite.role},
        )
        return membership
