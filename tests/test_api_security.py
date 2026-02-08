import pytest
from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator

from apps.documents.models import Document
from apps.documents.services import CollabTokenService
from config.asgi import application


@pytest.mark.django_db
def test_unauthorized_document_access_returns_404(api_client, user_factory):
    owner = user_factory("owner_api")
    outsider = user_factory("outsider_api")

    document = Document.objects.create(title="Secure Doc", owner=owner)

    api_client.force_login(outsider)
    response = api_client.get(f"/api/docs/{document.id}/")

    assert response.status_code == 404


@pytest.mark.django_db(transaction=True)
def test_ws_connect_rejects_non_member(user_factory):
    owner = user_factory("ws_owner")
    outsider = user_factory("ws_outsider")
    document = Document.objects.create(title="WS Secure", owner=owner)

    token, _ = CollabTokenService.mint(user_id=outsider.id, doc_id=str(document.id), role="viewer")

    async def run_check():
        communicator = WebsocketCommunicator(application, f"/ws/docs/{document.id}/?token={token}")
        connected, _ = await communicator.connect()
        assert connected is False

    async_to_sync(run_check)()
