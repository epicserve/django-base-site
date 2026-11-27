from ._base import *  # noqa: F403
from ._base import BASE_DIR, content_security_policy

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

# Run Celery tasks in-process, so emails (queued by apps.base.utils.email.queue_email) land in `mail.outbox` without a
# broker or worker (CI's e2e job runs no Redis), and a task that raises fails the test that queued it.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Use pre-built production assets instead of the Vite dev server
VITE_DEV_MODE = False
VITE_MANIFEST_FILE = BASE_DIR / "public" / "static" / "dist" / "js" / ".vite" / "manifest.json"
# _base.py built the policy with the Vite dev server allowed when DEBUG is on, so build it again for the built assets.
SECURE_CSP = content_security_policy(vite_dev_mode=False)

# The CI e2e job runs the web container with --no-deps, so Silo isn't
# available; swap the default storage to an in-memory backend so any test
# that touches default_storage doesn't hang trying to reach silo:9000.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# The live server speaks plain HTTP, and CI runs it with DEBUG off, which turns these on: SECURE_SSL_REDIRECT would send
# the browser to https://, which nothing serves. Pin them off, as with DEBUG on.
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

# Never report to Sentry, even with SENTRY_DSN in .env.
SENTRY_DSN = ""
