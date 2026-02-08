import pytest
import jwt
from django.conf import settings
from django.utils import timezone

from apps.documents.services import CollabTokenError, CollabTokenService


@pytest.mark.django_db
def test_collab_token_doc_binding(user_factory):
    user = user_factory("token_user")

    token, _expires_at = CollabTokenService.mint(user_id=user.id, doc_id="doc-1", role="viewer")
    claims = CollabTokenService.verify(token, "doc-1")

    assert claims.user_id == user.id
    assert claims.doc_id == "doc-1"

    with pytest.raises(CollabTokenError):
        CollabTokenService.verify(token, "doc-2")


@pytest.mark.django_db
def test_collab_token_rejects_expired(user_factory):
    user = user_factory("expired_user")
    expired_claims = {
        "sub": str(user.id),
        "user_id": user.id,
        "doc_id": "doc-1",
        "role": "viewer",
        "exp": int((timezone.now().timestamp()) - 10),
        "jti": "expired-jti",
    }
    token = jwt.encode(expired_claims, settings.SECRET_KEY, algorithm="HS256")

    with pytest.raises(CollabTokenError):
        CollabTokenService.verify(token, "doc-1")
