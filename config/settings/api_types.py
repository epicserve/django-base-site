"""
Settings for `just generate_api_types`, which exports the OpenAPI specs the SPA's TypeScript types come from.

Everything that changes the generated specs is pinned here, so the checked-in types don't depend on anyone's `.env`.
"""

from ._base import *  # noqa: F403
from ._base import INSTALLED_APPS

# Provides django-ninja's `export_openapi_schema` management command.
INSTALLED_APPS = [*INSTALLED_APPS, "ninja"]

# The billing router is only mounted when billing is on, but the SPA calls it, so its routes belong in the spec.
# Startup validates these settings without calling Stripe, so placeholders are enough.
BILLING_ENABLED = True
BILLING_PLANS: list[dict] = []
BILLING_FEATURES: list[dict] = []
STRIPE_SECRET_KEY = "sk_test_generate_api_types"  # noqa: S105 (a placeholder, never sent anywhere)
STRIPE_PUBLISHABLE_KEY = "pk_test_generate_api_types"
STRIPE_WEBHOOK_SECRET = "whsec_generate_api_types"  # noqa: S105 (a placeholder, never sent anywhere)

# allauth only builds its spec when it serves it. The SPA uses the browser client only, and with a single client
# allauth writes `browser` into each path instead of leaving a `{client}` placeholder.
HEADLESS_SERVE_SPECIFICATION = True
HEADLESS_CLIENTS = ("browser",)
