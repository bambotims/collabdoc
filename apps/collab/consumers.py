from __future__ import annotations

import logging
import os
import time
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.http import Http404
from pycrdt import Doc, YMessageType, YSyncMessageType, read_message
from pycrdt.websocket.django_channels_consumer import YjsConsumer

from apps.collab.services import PostgresYStore
from apps.documents.models import DocumentRole
from apps.documents.services import ACLService, CollabTokenError, CollabTokenService

logger = logging.getLogger(__name__)
User = get_user_model()

MAX_MESSAGE_BYTES = int(os.getenv("WS_MAX_MESSAGE_BYTES", str(1024 * 1024)))
MAX_MESSAGES_PER_SECOND = int(os.getenv("WS_MAX_MESSAGES_PER_SECOND", "50"))
MAX_CONNECTIONS_PER_USER_DOC = int(os.getenv("WS_MAX_CONNECTIONS_PER_USER_DOC", "5"))


class DocYjsConsumer(YjsConsumer):
    doc_id: str
    user_id: int
    role: str

    def make_room_name(self) -> str:
        return f"doc:{self.doc_id}"

    async def make_ydoc(self) -> Doc:
        return await database_sync_to_async(PostgresYStore.build_doc)(document_id=self.doc_id)

    async def connect(self) -> None:
        doc_id = self.scope["url_route"]["kwargs"].get("doc_id")
        self.doc_id = str(doc_id)

        query_string = self.scope.get("query_string", b"").decode("utf-8")
        token = parse_qs(query_string).get("token", [None])[0]
        if not token:
            await self.close(code=4401)
            return

        try:
            claims = CollabTokenService.verify(token, self.doc_id)
        except CollabTokenError:
            await self.close(code=4403)
            return

        user = await database_sync_to_async(User.objects.filter(pk=claims.user_id).first)()
        if user is None or not user.is_active:
            await self.close(code=4403)
            return

        allowed = await database_sync_to_async(ACLService.check)(
            user=user,
            doc_id=self.doc_id,
            required_role=DocumentRole.VIEWER,
        )
        if not allowed:
            await self.close(code=4403)
            return

        self.scope["user"] = user
        self.user_id = user.id
        self.role = claims.role

        if not await self._consume_connect_quota():
            await self.close(code=4429)
            return

        if not await self._acquire_connection_slot():
            await self.close(code=4429)
            return

        logger.info(
            "ws_connect",
            extra={"doc_id": self.doc_id, "user_id": self.user_id, "role": self.role},
        )
        await super().connect()

    async def disconnect(self, code) -> None:
        try:
            await super().disconnect(code)
        finally:
            await self._release_connection_slot()

    async def receive(self, text_data=None, bytes_data=None):
        if bytes_data is not None:
            if len(bytes_data) > MAX_MESSAGE_BYTES:
                await self.close(code=4400)
                return

            if not await self._consume_message_quota():
                await self.close(code=4429)
                return

            if bytes_data and bytes_data[0] == YMessageType.SYNC and len(bytes_data) > 1:
                if bytes_data[1] == YSyncMessageType.SYNC_UPDATE:
                    if self.role not in {DocumentRole.OWNER, DocumentRole.EDITOR}:
                        await self.close(code=4403)
                        return
                    update_payload = read_message(bytes_data[2:])
                    await database_sync_to_async(PostgresYStore.append_update)(
                        document_id=self.doc_id,
                        update_bytes=update_payload,
                        actor_id=self.user_id,
                    )
                    logger.info(
                        "update_persist",
                        extra={
                            "doc_id": self.doc_id,
                            "user_id": self.user_id,
                            "size": len(update_payload),
                        },
                    )

        await super().receive(text_data=text_data, bytes_data=bytes_data)

    async def _consume_connect_quota(self) -> bool:
        now_bucket = int(time.time() // 60)
        key = f"ws_connect:{self.user_id}:{self.doc_id}:{now_bucket}"
        return await database_sync_to_async(_increment_with_limit)(key, 120, 70)

    async def _consume_message_quota(self) -> bool:
        now_bucket = int(time.time())
        key = f"ws_msg:{self.user_id}:{self.doc_id}:{now_bucket}"
        return await database_sync_to_async(_increment_with_limit)(key, MAX_MESSAGES_PER_SECOND, 3)

    async def _acquire_connection_slot(self) -> bool:
        key = f"ws_open:{self.user_id}:{self.doc_id}"
        return await database_sync_to_async(_acquire_slot)(key, MAX_CONNECTIONS_PER_USER_DOC)

    async def _release_connection_slot(self) -> None:
        if not getattr(self, "user_id", None):
            return
        key = f"ws_open:{self.user_id}:{self.doc_id}"
        await database_sync_to_async(_release_slot)(key)


def _increment_with_limit(key: str, limit: int, ttl_seconds: int) -> bool:
    added = cache.add(key, 1, timeout=ttl_seconds)
    if added:
        count = 1
    else:
        count = cache.incr(key)
    return int(count) <= limit


def _acquire_slot(key: str, limit: int) -> bool:
    added = cache.add(key, 1, timeout=7200)
    if added:
        return True
    count = cache.incr(key)
    if int(count) > limit:
        try:
            cache.decr(key)
        except ValueError:
            cache.set(key, limit, timeout=7200)
        return False
    return True


def _release_slot(key: str) -> None:
    try:
        count = cache.decr(key)
        if int(count) <= 0:
            cache.delete(key)
    except ValueError:
        cache.delete(key)
