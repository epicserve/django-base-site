from ._base import *  # noqa: F403, F401
from ._base import BASE_DIR

PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)

# e2e tests should never hit Stripe.
BILLING_ENABLED = False
BILLING_PLANS: list[dict] = []
BILLING_FEATURES: list[dict] = []

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

# The CI e2e job runs the web container with --no-deps, so MinIO isn't
# available; swap the default storage to an in-memory backend so any test
# that touches default_storage doesn't hang trying to reach minio:9000.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
