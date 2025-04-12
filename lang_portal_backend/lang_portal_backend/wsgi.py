"""
WSGI config for lang_portal_backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lang_portal_backend.settings')

print("*" * 80)
print("WSGI STARTUP: Django is initializing with settings module:", os.environ.get('DJANGO_SETTINGS_MODULE'))
print("*" * 80)

application = get_wsgi_application()

print("*" * 80)
print("WSGI STARTUP COMPLETE: Django application is ready")
print("*" * 80)
