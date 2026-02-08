from django.contrib import admin
from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from apps.accounts.views import CsrfView, HealthView, LoginView, LogoutView, MeView, RegisterView, WorkerHealthView
from apps.comments.views import CommentReopenView, CommentResolveView, DocumentCommentsView
from apps.documents.views import (
    AcceptInviteView,
    DocumentCollabTokenView,
    DocumentInvitesView,
    DocumentMemberDetailView,
    DocumentMembersView,
    DocumentViewSet,
)
from apps.snapshots.views import DocumentSnapshotsView, SnapshotRestoreView
from config.views import FrontendAppView

router = DefaultRouter()
router.register("docs", DocumentViewSet, basename="doc")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/login", LoginView.as_view(), name="api-login"),
    path("api/auth/register", RegisterView.as_view(), name="api-register"),
    path("api/auth/logout", LogoutView.as_view(), name="api-logout"),
    path("api/auth/csrf", CsrfView.as_view(), name="api-csrf"),
    path("api/auth/me", MeView.as_view(), name="api-me"),
    path("api/health", HealthView.as_view(), name="api-health"),
    path("api/worker-health", WorkerHealthView.as_view(), name="api-worker-health"),
    path("api/", include(router.urls)),
    path("api/docs/<uuid:doc_id>/members", DocumentMembersView.as_view(), name="api-doc-members"),
    path(
        "api/docs/<uuid:doc_id>/members/<int:member_id>",
        DocumentMemberDetailView.as_view(),
        name="api-doc-member-detail",
    ),
    path("api/docs/<uuid:doc_id>/invites", DocumentInvitesView.as_view(), name="api-doc-invites"),
    path("api/docs/<uuid:doc_id>/collab-token", DocumentCollabTokenView.as_view(), name="api-doc-collab-token"),
    path("api/invites/accept", AcceptInviteView.as_view(), name="api-invite-accept"),
    path("api/docs/<uuid:doc_id>/comments", DocumentCommentsView.as_view(), name="api-doc-comments"),
    path(
        "api/docs/<uuid:doc_id>/comments/<int:thread_id>/resolve",
        CommentResolveView.as_view(),
        name="api-doc-comment-resolve",
    ),
    path(
        "api/docs/<uuid:doc_id>/comments/<int:thread_id>/reopen",
        CommentReopenView.as_view(),
        name="api-doc-comment-reopen",
    ),
    path("api/docs/<uuid:doc_id>/snapshots", DocumentSnapshotsView.as_view(), name="api-doc-snapshots"),
    path(
        "api/docs/<uuid:doc_id>/snapshots/<int:snapshot_id>/restore",
        SnapshotRestoreView.as_view(),
        name="api-doc-snapshot-restore",
    ),
    path("", FrontendAppView.as_view(), name="frontend-root"),
    re_path(r"^(?!api/|admin/).*$", FrontendAppView.as_view(), name="frontend-app"),
]
