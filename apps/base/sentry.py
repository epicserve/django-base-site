"""Error reporting to Sentry, which is on when SENTRY_DSN is set."""

from django.conf import settings

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration


def init_sentry() -> None:
    """Report errors from Django and Celery to Sentry, if SENTRY_DSN is set. `BaseConfig.ready()` calls it."""
    if not settings.SENTRY_DSN:
        return
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.INSTANCE,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        # Request bodies hold what people type, such as the email addresses they invite. Without `data_collection` (or
        # the older `send_default_pii`), Sentry already leaves out who the user is, their IP address, and cookies.
        # Local variables in a stack trace are still sent, with passwords, tokens and keys filtered.
        # apps/base/tests/test_sentry.py checks all of that.
        max_request_body_size="never",
    )
