from ._base import *  # noqa: F403

PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)

# Tests should never hit Stripe and must not require real price IDs. Tests that exercise the billing layer turn it on
# with `@override_settings(**BILLING_SETTINGS)` from apps/billing/recipes.py.
BILLING_ENABLED = False
BILLING_PLANS: list[dict] = []
BILLING_FEATURES: list[dict] = []

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

SESSION_ENGINE: str = "django.contrib.sessions.backends.cached_db"

# Run Celery tasks in-process, so emails (queued by apps.base.utils.email.queue_email) land in `mail.outbox` without a
# broker or worker, and a task that raises fails the test that queued it.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# A git worktree's .env moves these to its own ports (scripts/worktree). Tests expect the defaults.
SESSION_COOKIE_NAME = "sessionid"
VITE_SERVER_PORT = "3000"
MAILPIT_PORT = 8025
SILO_CONSOLE_PORT = 9001

# These default on when DEBUG is off, as it is in CI, and off with a developer's DEBUG=on. The test client speaks plain
# HTTP, so SECURE_SSL_REDIRECT would answer every request with a redirect to https://. Pin all of them off so tests
# behave the same everywhere; apps/base/tests/test_https_settings.py covers the defaults.
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

# Never report to Sentry, even with SENTRY_DSN in .env.
SENTRY_DSN = ""
