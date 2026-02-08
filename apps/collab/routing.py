from django.urls import re_path

from .consumers import DocYjsConsumer

websocket_urlpatterns = [
    re_path(r"^ws/docs/(?P<doc_id>[0-9a-f\-]+)/?$", DocYjsConsumer.as_asgi()),
]
