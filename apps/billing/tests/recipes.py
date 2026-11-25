"""
Test data for billing.

A test class turns billing on with `@override_settings(**BILLING_SETTINGS)`, which also declares the plans and features
below, and builds customers and subscriptions with `make_customer` and `make_subscription`. A test that needs a
different catalog overrides just that setting. A plain (non-`BaseTest`) class sets them with the `settings` fixture.
"""

from datetime import timedelta
from itertools import count

from django.utils import timezone

from apps.billing.constants import SubscriptionStatus
from apps.billing.models import BillingCustomer, Subscription
from apps.organizations.models import Organization

FREE_PLAN = {
    "key": "free",
    "name": "Free",
    "is_free": True,
    "is_default": True,
    "features": {"max_team_count": 1, "advanced_reporting": False},
}
PRO_PLAN = {
    "key": "pro",
    "name": "Pro",
    "monthly_price_id": "price_pro_monthly",
    "annual_price_id": "price_pro_annual",
    "trial_days": 14,
    "seat_based": True,
    "features": {"max_team_count": 10, "advanced_reporting": True},
}
BILLING_PLANS = [FREE_PLAN, PRO_PLAN]

# `max_team_count` defaults to 0, below the free plan's 1, so a test can tell the feature's default from the plan's.
BILLING_FEATURES = [
    {"key": "max_team_count", "label": "Teams", "type": "limit", "default": 0},
    {"key": "advanced_reporting", "label": "Reporting", "type": "bool", "default": False},
]

BILLING_SETTINGS = {
    "BILLING_ENABLED": True,
    "BILLING_PLANS": BILLING_PLANS,
    "BILLING_FEATURES": BILLING_FEATURES,
    "STRIPE_SECRET_KEY": "sk_test_dummy",  # noqa: S105
    "STRIPE_WEBHOOK_SECRET": "whsec_dummy",  # noqa: S105
}

_numbers = count(1)


def make_customer(org: Organization, **fields) -> BillingCustomer:
    """Make `org`'s Stripe customer, with a unique `stripe_customer_id` unless one is passed."""
    fields.setdefault("stripe_customer_id", f"cus_recipe_{next(_numbers)}")
    return BillingCustomer.objects.create(organization=org, **fields)


def make_subscription(
    org: Organization,
    *,
    plan_key: str = "pro",
    status: str | None = None,
    trial_ends_in: timedelta | None = None,
    **fields,
) -> Subscription:
    """
    Make `org`'s subscription to `plan_key`, with a unique `stripe_subscription_id` unless one is passed.

    `trial_ends_in` sets `trial_end` that long from now. `status` defaults to trialing with `trial_ends_in` and to
    active without it. Any other keyword sets a `Subscription` field, such as `quantity`.
    """
    if status is None:
        status = SubscriptionStatus.TRIALING if trial_ends_in is not None else SubscriptionStatus.ACTIVE
    if trial_ends_in is not None:
        fields["trial_end"] = timezone.now() + trial_ends_in
    fields.setdefault("stripe_subscription_id", f"sub_recipe_{next(_numbers)}")
    return Subscription.objects.create(organization=org, plan_key=plan_key, status=status, **fields)
