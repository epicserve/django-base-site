from ._base import *  # noqa: F403

PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)

AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

DATABASES["default"] = {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}  # noqa: F405

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
