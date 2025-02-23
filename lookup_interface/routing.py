from . import consumers
from django.urls import re_path

websocket_urlpatterns = [
    re_path(r'ws/lookup-server/', consumers.LookupConsumer.as_asgi())
]