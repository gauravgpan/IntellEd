"""
WSGI config for the ThinkTurf backend.

This is the entry point Apache's mod_wsgi loads in production
(see backend/apache/thinkturf.conf).
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
