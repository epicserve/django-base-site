from ._base import *  # noqa: F403

PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

SESSION_ENGINE: str = "django.contrib.sessions.backends.cached_db"
