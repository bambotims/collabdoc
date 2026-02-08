from __future__ import annotations

from django.http import Http404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.collab.models import DocSnapshot, SnapshotKind
from apps.documents.models import DocumentRole
from apps.documents.services import ACLService

from .serializers import SnapshotSerializer
from .services import SnapshotService


class DocumentSnapshotsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, doc_id):
        _document, _role = ACLService.get_document_or_404(user=request.user, doc_id=doc_id, required_role=DocumentRole.VIEWER)
        snapshots = DocSnapshot.objects.filter(document_id=doc_id).order_by("-seq", "-created_at")
        return Response(SnapshotSerializer(snapshots, many=True).data)

    def post(self, request, doc_id):
        _document, _role = ACLService.get_document_or_404(user=request.user, doc_id=doc_id, required_role=DocumentRole.EDITOR)
        snapshot = SnapshotService.create(
            document_id=str(doc_id),
            actor_id=request.user.id,
            kind=SnapshotKind.MANUAL,
            metadata={"reason": "manual"},
        )
        return Response(SnapshotSerializer(snapshot).data, status=status.HTTP_201_CREATED)


class SnapshotRestoreView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, doc_id, snapshot_id):
        _document, _role = ACLService.get_document_or_404(user=request.user, doc_id=doc_id, required_role=DocumentRole.EDITOR)
        try:
            restored = SnapshotService.restore(document_id=str(doc_id), snapshot_id=snapshot_id, actor_id=request.user.id)
        except DocSnapshot.DoesNotExist as exc:
            raise Http404("Snapshot not found") from exc
        return Response(SnapshotSerializer(restored).data)
