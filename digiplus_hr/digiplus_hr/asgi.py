import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import manage_users.routing  # On va créer ce fichier

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digiplus_hr.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # HTTP classique
    "websocket": AuthMiddlewareStack(
        URLRouter(
            manage_users.routing.websocket_urlpatterns
        )
    ),
})
