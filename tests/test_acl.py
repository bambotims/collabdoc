import pytest

from apps.documents.models import Document, DocumentMembership, DocumentRole
from apps.documents.services import ACLService


@pytest.mark.django_db
def test_acl_matrix(user_factory):
    owner = user_factory("owner")
    editor = user_factory("editor")
    commenter = user_factory("commenter")
    viewer = user_factory("viewer")
    outsider = user_factory("outsider")

    document = Document.objects.create(title="Doc", owner=owner)
    DocumentMembership.objects.create(document=document, user=owner, role=DocumentRole.OWNER)
    DocumentMembership.objects.create(document=document, user=editor, role=DocumentRole.EDITOR)
    DocumentMembership.objects.create(document=document, user=commenter, role=DocumentRole.COMMENTER)
    DocumentMembership.objects.create(document=document, user=viewer, role=DocumentRole.VIEWER)

    assert ACLService.check(user=owner, doc_id=str(document.id), required_role=DocumentRole.OWNER)
    assert ACLService.check(user=editor, doc_id=str(document.id), required_role=DocumentRole.EDITOR)
    assert ACLService.check(user=commenter, doc_id=str(document.id), required_role=DocumentRole.COMMENTER)
    assert ACLService.check(user=viewer, doc_id=str(document.id), required_role=DocumentRole.VIEWER)

    assert not ACLService.check(user=viewer, doc_id=str(document.id), required_role=DocumentRole.EDITOR)
    assert not ACLService.check(user=commenter, doc_id=str(document.id), required_role=DocumentRole.EDITOR)
    assert not ACLService.check(user=outsider, doc_id=str(document.id), required_role=DocumentRole.VIEWER)
