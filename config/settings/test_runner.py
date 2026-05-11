from ._base import *  # noqa: F403

PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)

# Tests should never hit Stripe and must not require real price IDs. Tests
# that exercise the billing layer flip these via the pytest `settings` fixture.
BILLING_ENABLED = False
BILLING_PLANS: list[dict] = []
BILLING_FEATURES: list[dict] = []

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

SESSION_ENGINE: str = "django.contrib.sessions.backends.cached_db"
