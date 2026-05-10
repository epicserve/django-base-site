"""
Feature-gating helpers.

Resolution order for `org_feature_value(org, feature_key)`:

  1. BILLING_ENABLED=False → return the feature's declared default. The starter
     template runs out of the box without Stripe credentials, and gates fall
     through to whatever the project marked as the unrestricted default.
  2. The org has no Subscription, or the subscription's status isn't active →
     fall back to the default plan's value (or the feature default).
  3. Active subscription → return the plan's `features.get(feature_key)` or
     the feature default if that plan didn't override it.

Past-due / canceled / unpaid subscriptions don't grant feature access — the
user falls back to the default plan. Stripe's Customer Portal handles the
dunning emails; we surface a banner in the UI.
"""

import functools
from typing import Any

from django.conf import settings
from django.core.exceptions import PermissionDenied

from apps.base.permissions import require_org_selected
from apps.billing.features import get_feature
from apps.billing.plans import get_default_plan, get_plan


def _resolve_plan(org):
    """Return the (plan, is_active) tuple for an org's subscription state."""
    sub = getattr(org, "subscription", None)
    if sub is None:
        return get_default_plan(), False
    if not sub.is_active:
        return get_default_plan(), False
    return get_plan(sub.plan_key) or get_default_plan(), True


def org_feature_value(org, feature_key: str) -> Any:
    """Resolve the value of `feature_key` for `org`."""
    feature = get_feature(feature_key)
    fallback = feature.default if feature is not None else False

    if not getattr(settings, "BILLING_ENABLED", False):
        return fallback

    if org is None:
        return fallback

    plan, _is_active = _resolve_plan(org)
    if plan is None:
        return fallback
    return plan.features.get(feature_key, fallback)


def org_has_feature(org, feature_key: str) -> bool:
    """Bool wrapper. For 'limit' features, returns value > 0."""
    value = org_feature_value(org, feature_key)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value > 0
    return value is not None and value != ""


def requires_feature(feature_key: str):
    """
    Ninja view decorator that 402-Payment-Required's when a feature is missing.

    RFC 9110 carves out 402 for exactly this case; the SPA error handler
    routes 402 → upgrade prompt.
    """

    def decorator(view):
        @functools.wraps(view)
        def wrapper(request, *args, **kwargs):
            from ninja.errors import HttpError

            org = require_org_selected(request)
            if not org_has_feature(org, feature_key):
                raise HttpError(402, f"This feature requires an upgrade ({feature_key}).") from PermissionDenied()
            return view(request, *args, **kwargs)

        return wrapper

    return decorator


def org_billing_summary(org) -> dict:
    """Return the dict shape the SPA expects under `app_context.billing`."""
    if not getattr(settings, "BILLING_ENABLED", False):
        from apps.billing.features import get_features

        return {
            "enabled": False,
            "publishable_key": "",
            "plan": None,
            "status": None,
            "billing_cycle": None,
            "trial_end": None,
            "cancel_at_period_end": False,
            "features": {f.key: f.default for f in get_features()},
        }

    sub = getattr(org, "subscription", None) if org is not None else None
    plan, _ = _resolve_plan(org) if org is not None else (None, False)

    from apps.billing.features import get_features

    return {
        "enabled": True,
        "publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
        "plan": {"key": plan.key, "name": plan.name} if plan is not None else None,
        "status": sub.status if sub is not None else None,
        "billing_cycle": sub.billing_cycle if sub is not None else None,
        "trial_end": sub.trial_end.isoformat() if sub is not None and sub.trial_end else None,
        "cancel_at_period_end": bool(sub.cancel_at_period_end) if sub is not None else False,
        "features": {f.key: org_feature_value(org, f.key) for f in get_features()},
    }
