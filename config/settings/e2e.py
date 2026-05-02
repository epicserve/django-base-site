from ._base import *  # noqa: F403, F401
from ._base import BASE_DIR

PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Use database-backed sessions since DummyCache can't store session data
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# Use pre-built production assets instead of the Vite dev server
VITE_DEV_MODE = False
VITE_MANIFEST_FILE = BASE_DIR / "public" / "static" / "dist" / "js" / ".vite" / "manifest.json"
