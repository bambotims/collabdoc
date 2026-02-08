import base64

import pytest

from apps.documents.models import Document, DocumentMembership, DocumentRole


@pytest.mark.django_db
def test_comment_anchor_round_trip(api_client, user_factory):
    user = user_factory("comment_user")
    document = Document.objects.create(title="Commented", owner=user)
    DocumentMembership.objects.create(document=document, user=user, role=DocumentRole.OWNER)

    api_client.force_login(user)

    start_anchor = base64.b64encode(b"anchor:start").decode("ascii")
    end_anchor = base64.b64encode(b"anchor:end").decode("ascii")

    response = api_client.post(
        f"/api/docs/{document.id}/comments",
        {
            "body": "Looks good",
            "start_rel_b64": start_anchor,
            "end_rel_b64": end_anchor,
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["anchor"]["start_rel_b64"] == start_anchor
    assert response.data["anchor"]["end_rel_b64"] == end_anchor
