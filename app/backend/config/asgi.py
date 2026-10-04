"""ASGI config for the ThinkTurf backend (kept for dev-server parity; prod serves via WSGI/Apache)."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()
