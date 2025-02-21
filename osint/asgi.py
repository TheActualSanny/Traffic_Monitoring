"""
ASGI config for osint project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from tools import routing as tool
from lookup_interface import routing as lookup

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'osint.settings')

application = ProtocolTypeRouter({
    'http' : get_asgi_application(),
    'websocket' : AuthMiddlewareStack(
        URLRouter(
            tool.websocket_urlpatterns + lookup.websocket_urlpatterns
        )
    )
})
