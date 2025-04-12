"""
Django settings for lang_portal_backend project - Docker configuration.
"""

from .settings import *
import time
import os

# Database configuration for Docker - Using SQLite instead of PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'words.db',
    }
}

# Debug mode
DEBUG = os.getenv('DEBUG', 'False') == '1'

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True
