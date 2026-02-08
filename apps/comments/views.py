from __future__ import annotations

from django.http import Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import record_audit_event
from apps.documents.models import DocumentRole
from apps.documents.services import ACLService

from .models import CommentAnchor, CommentStatus, CommentThread
from .serializers import CommentCreateSerializer, CommentThreadSerializer


class DocumentCommentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, doc_id):
        _document, _role = ACLService.get_document_or_404(user=request.user, doc_id=doc_id, required_role=DocumentRole.VIEWER)
        threads = CommentThread.objects.filter(document_id=doc_id).select_related("anchor")
        return Response(CommentThreadSerializer(threads, many=True).data)

    def post(self, request, doc_id):
        _document, _role = ACLService.get_document_or_404(user=request.user, doc_id=doc_id, required_role=DocumentRole.COMMENTER)
        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        start_rel_bytes, end_rel_bytes = serializer.decode_anchor_bytes()

        thread = CommentThread.objects.create(
            document_id=doc_id,
            author=request.user,
            body=serializer.validated_data["body"],
            status=CommentStatus.OPEN,
        )
        CommentAnchor.objects.create(
            thread=thread,
            start_rel_bytes=start_rel_bytes,
            end_rel_bytes=end_rel_bytes,
        )

        record_audit_event(
            document_id=str(doc_id),
            actor_id=request.user.id,
            event_type="comment.created",
            payload={"thread_id": thread.id},
        )

        return Response(CommentThreadSerializer(thread).data, status=status.HTTP_201_CREATED)


class CommentResolveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, doc_id, thread_id):
        _document, _role = ACLService.get_document_or_404(user=request.user, doc_id=doc_id, required_role=DocumentRole.COMMENTER)
        thread = CommentThread.objects.filter(document_id=doc_id, pk=thread_id).first()
        if thread is None:
            raise Http404("Comment thread not found")
        thread.status = CommentStatus.RESOLVED
        thread.resolved_at = timezone.now()
        thread.resolved_by = request.user
        thread.save(update_fields=["status", "resolved_at", "resolved_by", "updated_at"])

        record_audit_event(
            document_id=str(doc_id),
            actor_id=request.user.id,
            event_type="comment.resolved",
            payload={"thread_id": thread.id},
        )
        return Response(CommentThreadSerializer(thread).data)


class CommentReopenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, doc_id, thread_id):
        _document, _role = ACLService.get_document_or_404(user=request.user, doc_id=doc_id, required_role=DocumentRole.COMMENTER)
        thread = CommentThread.objects.filter(document_id=doc_id, pk=thread_id).first()
        if thread is None:
            raise Http404("Comment thread not found")
        thread.status = CommentStatus.OPEN
        thread.resolved_at = None
        thread.resolved_by = None
        thread.save(update_fields=["status", "resolved_at", "resolved_by", "updated_at"])

        record_audit_event(
            document_id=str(doc_id),
            actor_id=request.user.id,
            event_type="comment.reopened",
            payload={"thread_id": thread.id},
        )
        return Response(CommentThreadSerializer(thread).data)
