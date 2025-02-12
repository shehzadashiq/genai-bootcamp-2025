import pytest
from django.conf import settings


@pytest.fixture(autouse=True)
def use_test_database(settings):
    """Configure test database"""
    settings.DATABASES["default"]["TEST"] = {
        "NAME": ":memory:",
        "MIRROR": False,
        "CHARSET": "utf8",
        "COLLATION": None,
        "SERIALIZE": False,
    }


@pytest.fixture(autouse=True)
def use_test_cache(settings):
    """Configure test cache"""
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",
        }
    }


@pytest.fixture(autouse=True)
def disable_throttling(settings):
    """Disable throttling for tests"""
    settings.REST_FRAMEWORK = {
        **settings.REST_FRAMEWORK,
        "DEFAULT_THROTTLE_CLASSES": [],
        "DEFAULT_THROTTLE_RATES": {},
    }
