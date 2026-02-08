from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import Http404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services import record_audit_event

from .models import Document, DocumentMembership, DocumentRole, InviteLink
from .serializers import (
    CollabTokenSerializer,
    DocumentMembershipSerializer,
    DocumentSerializer,
    DocumentWriteSerializer,
    InviteCreateSerializer,
    InviteIssuedSerializer,
    InviteSerializer,
)
from .services import ACLService, CollabTokenService, InviteService
from .throttles import CollabTokenThrottle, InviteCreateThrottle


User = get_user_model()


class DocumentViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    serializer_class = DocumentSerializer

    def get_queryset(self):
        user = self.request.user
        return Document.objects.filter(Q(owner=user) | Q(memberships__user=user)).distinct()

    def get_serializer_class(self):
        if self.action in {"create", "partial_update", "update"}:
            return DocumentWriteSerializer
        return DocumentSerializer

    def get_object_with_role(self, required_role: str = DocumentRole.VIEWER):
        document_id = self.kwargs.get("pk")
        return ACLService.get_document_or_404(user=self.request.user, doc_id=document_id, required_role=required_role)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = DocumentSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = Document.objects.create(title=serializer.validated_data["title"], owner=request.user)
        DocumentMembership.objects.update_or_create(
            document=document,
            user=request.user,
            defaults={"role": DocumentRole.OWNER},
        )
        output = DocumentSerializer(document, context={"request": request, "my_role": DocumentRole.OWNER})
        return Response(output.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        document, role = self.get_object_with_role(DocumentRole.VIEWER)
        serializer = DocumentSerializer(document, context={"request": request, "my_role": role})
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        document, _role = self.get_object_with_role(DocumentRole.EDITOR)
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if "title" in serializer.validated_data:
            document.title = serializer.validated_data["title"]
            document.save(update_fields=["title", "updated_at"])
        output = DocumentSerializer(document, context={"request": request})
        return Response(output.data)

    def destroy(self, request, *args, **kwargs):
        document, _role = self.get_object_with_role(DocumentRole.EDITOR)
        document.is_archived = True
        document.save(update_fields=["is_archived", "updated_at"])
        record_audit_event(
            document_id=str(document.id),
            actor_id=request.user.id,
            event_type="document.archived",
            payload={},
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk=None):
        document, role = self.get_object_with_role(DocumentRole.EDITOR)
        duplicate = Document.objects.create(
            title=f"{document.title} (Copy)",
            owner=request.user,
            is_archived=False,
        )
        DocumentMembership.objects.update_or_create(
            document=duplicate,
            user=request.user,
            defaults={"role": DocumentRole.OWNER},
        )
        record_audit_event(
            document_id=str(document.id),
            actor_id=request.user.id,
            event_type="document.duplicated",
            payload={"target_document_id": str(duplicate.id), "from_role": role},
        )
        serializer = DocumentSerializer(duplicate, context={"request": request, "my_role": DocumentRole.OWNER})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        document, _role = self.get_object_with_role(DocumentRole.EDITOR)
        if not document.is_archived:
            document.is_archived = True
            document.save(update_fields=["is_archived", "updated_at"])
            record_audit_event(
                document_id=str(document.id),
                actor_id=request.user.id,
                event_type="document.archived",
                payload={},
            )
        serializer = DocumentSerializer(document, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        document, _role = self.get_object_with_role(DocumentRole.EDITOR)
        if document.is_archived:
            document.is_archived = False
            document.save(update_fields=["is_archived", "updated_at"])
            record_audit_event(
                document_id=str(document.id),
                actor_id=request.user.id,
                event_type="document.restored",
                payload={},
            )
        serializer = DocumentSerializer(document, context={"request": request})
        return Response(serializer.data)


class DocumentMembersView(APIView):
    permission_classes = [IsAuthenticated]

    def get_document(self, doc_id: str, required_role: str):
        document, _role = ACLService.get_document_or_404(user=self.request.user, doc_id=doc_id, required_role=required_role)
        return document

    def get(self, request, doc_id):
        document = self.get_document(doc_id, DocumentRole.VIEWER)
        memberships = DocumentMembership.objects.filter(document=document).select_related("user")
        serializer = DocumentMembershipSerializer(memberships, many=True)
        return Response(serializer.data)

    def post(self, request, doc_id):
        document = self.get_document(doc_id, DocumentRole.OWNER)
        serializer = DocumentMembershipSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        member_user = serializer.validated_data["user"]
        role = serializer.validated_data["role"]
        if role == DocumentRole.OWNER and document.owner_id != member_user.id:
            raise Http404("Document not found")
        membership, _ = DocumentMembership.objects.update_or_create(
            document=document,
            user=member_user,
            defaults={"role": role},
        )
        record_audit_event(
            document_id=str(document.id),
            actor_id=request.user.id,
            event_type="document.member_changed",
            payload={"user_id": member_user.id, "role": role},
        )
        return Response(DocumentMembershipSerializer(membership).data, status=status.HTTP_201_CREATED)


class DocumentMemberDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, doc_id, member_id):
        document, _role = ACLService.get_document_or_404(user=request.user, doc_id=doc_id, required_role=DocumentRole.OWNER)
        membership = DocumentMembership.objects.filter(document=document, pk=member_id).select_related("user").first()
        if not membership:
            raise Http404("Member not found")
        serializer = DocumentMembershipSerializer(membership, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        record_audit_event(
            document_id=str(document.id),
            actor_id=request.user.id,
            event_type="document.member_changed",
            payload={"user_id": membership.user_id, "role": membership.role},
        )
        return Response(serializer.data)

    def delete(self, request, doc_id, member_id):
        document, _role = ACLService.get_document_or_404(user=request.user, doc_id=doc_id, required_role=DocumentRole.OWNER)
        membership = DocumentMembership.objects.filter(document=document, pk=member_id).first()
        if not membership:
            raise Http404("Member not found")
        if membership.user_id == document.owner_id:
            return Response({"detail": "Cannot remove owner membership"}, status=status.HTTP_400_BAD_REQUEST)
        membership.delete()
        record_audit_event(
            document_id=str(document.id),
            actor_id=request.user.id,
            event_type="document.member_removed",
            payload={"member_id": member_id},
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentInvitesView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [InviteCreateThrottle]

    def get(self, request, doc_id):
        document, _role = ACLService.get_document_or_404(user=request.user, doc_id=doc_id, required_role=DocumentRole.EDITOR)
        invites = InviteLink.objects.filter(document=document)
        serializer = InviteSerializer(invites, many=True)
        return Response(serializer.data)

    def post(self, request, doc_id):
        document, _role = ACLService.get_document_or_404(user=request.user, doc_id=doc_id, required_role=DocumentRole.EDITOR)
        serializer = InviteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invite, token = InviteService.create_invite(
            document=document,
            role=serializer.validated_data["role"],
            expires_at=serializer.validated_data["expires_at"],
            max_uses=serializer.validated_data["max_uses"],
            created_by=request.user,
        )
        record_audit_event(
            document_id=str(document.id),
            actor_id=request.user.id,
            event_type="document.invite_created",
            payload={"invite_id": invite.id, "role": invite.role, "expires_at": invite.expires_at.isoformat()},
        )
        output = InviteIssuedSerializer({
            "id": invite.id,
            "role": invite.role,
            "expires_at": invite.expires_at,
            "max_uses": invite.max_uses,
            "use_count": invite.use_count,
            "created_by_id": invite.created_by_id,
            "created_at": invite.created_at,
            "token": token,
        })
        return Response(output.data, status=status.HTTP_201_CREATED)


class DocumentCollabTokenView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [CollabTokenThrottle]

    def post(self, request, doc_id):
        _document, role = ACLService.get_document_or_404(user=request.user, doc_id=doc_id, required_role=DocumentRole.VIEWER)
        token, expires_at = CollabTokenService.mint(user_id=request.user.id, doc_id=str(doc_id), role=role)
        serializer = CollabTokenSerializer({"token": token, "expires_at": expires_at, "role": role})
        return Response(serializer.data)


class AcceptInviteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        raw_token = request.data.get("token")
        if not raw_token:
            return Response({"detail": "token is required"}, status=status.HTTP_400_BAD_REQUEST)
        membership = InviteService.consume_invite(raw_token=raw_token, user=request.user)
        record_audit_event(
            document_id=str(membership.document_id),
            actor_id=request.user.id,
            event_type="document.invite_consumed",
            payload={"membership_id": membership.id, "role": membership.role},
        )
        return Response(DocumentMembershipSerializer(membership).data)
