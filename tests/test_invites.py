import pytest
from django.http import Http404
from django.utils import timezone

from apps.documents.models import Document, DocumentRole
from apps.documents.services import InviteService


@pytest.mark.django_db
def test_invite_expiry_and_role(user_factory):
    owner = user_factory("invite_owner")
    member = user_factory("invite_member")

    document = Document.objects.create(title="Invite Doc", owner=owner)

    invite, raw_token = InviteService.create_invite(
        document=document,
        role=DocumentRole.COMMENTER,
        expires_at=timezone.now() + timezone.timedelta(hours=1),
        max_uses=1,
        created_by=owner,
    )

    membership = InviteService.consume_invite(raw_token=raw_token, user=member)

    assert membership.role == DocumentRole.COMMENTER
    invite.refresh_from_db()
    assert invite.use_count == 1

    with pytest.raises(Http404):
        InviteService.consume_invite(raw_token=raw_token, user=member)


@pytest.mark.django_db
def test_invite_rejects_expired(user_factory):
    owner = user_factory("expired_owner")
    member = user_factory("expired_member")

    document = Document.objects.create(title="Expired Invite", owner=owner)
    _invite, raw_token = InviteService.create_invite(
        document=document,
        role=DocumentRole.VIEWER,
        expires_at=timezone.now() - timezone.timedelta(minutes=1),
        max_uses=1,
        created_by=owner,
    )

    with pytest.raises(Http404):
        InviteService.consume_invite(raw_token=raw_token, user=member)
