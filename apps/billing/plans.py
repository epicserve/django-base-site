"""
Subscription plan registry.

Plans are declared in `settings.BILLING_PLANS`. Each entry is a plain dict (the
cheapest thing to type by hand in `_base.py`); entries are normalized into
`Plan` dataclasses for attribute access. Mirrors the
`apps.notifications.categories` pattern: settings load identically in every
process, so there is no per-process drift, and downstream apps add plans by
extending the setting.

Example:
    BILLING_PLANS = [
        {
            "key": "free",
            "name": "Free",
            "description": "For personal projects.",
            "is_free": True,
            "is_default": True,
            "features": {"max_team_count": 1, "advanced_reporting": False},
        },
        {
            "key": "pro",
            "name": "Pro",
            "description": "For growing teams.",
            "monthly_price_id": env("STRIPE_PRICE_PRO_MONTHLY", default=""),
            "annual_price_id": env("STRIPE_PRICE_PRO_ANNUAL", default=""),
            "monthly_price_cents": 2900,
            "annual_price_cents": 29000,
            "currency": "usd",
            "trial_days": 14,
            "seat_based": True,
            "features": {"max_team_count": 10, "advanced_reporting": True},
        },
    ]

When `BILLING_ENABLED=True`, `apps.billing.apps.BillingConfig.ready()` validates
that every non-free plan has at least one of `monthly_price_id` /
`annual_price_id` set, so misconfiguration fails loudly at startup.

"""

from dataclasses import dataclass, field
from typing import Any

from django.conf import settings


@dataclass(frozen=True)
class Plan:
    key: str
    name: str
    description: str = ""
    monthly_price_id: str = ""
    annual_price_id: str = ""
    monthly_price_cents: int = 0
    annual_price_cents: int = 0
    currency: str = "usd"
    trial_days: int = 0
    seat_based: bool = False
    is_free: bool = False
    is_default: bool = False
    is_highlighted: bool = False
    features: dict[str, Any] = field(default_factory=dict)


def _normalize(entry: dict) -> Plan:
    return Plan(
        key=entry["key"],
        name=entry.get("name", entry["key"]),
        description=entry.get("description", ""),
        monthly_price_id=entry.get("monthly_price_id", ""),
        annual_price_id=entry.get("annual_price_id", ""),
        monthly_price_cents=entry.get("monthly_price_cents", 0),
        annual_price_cents=entry.get("annual_price_cents", 0),
        currency=entry.get("currency", "usd"),
        trial_days=entry.get("trial_days", 0),
        seat_based=entry.get("seat_based", False),
        is_free=entry.get("is_free", False),
        is_default=entry.get("is_default", False),
        is_highlighted=entry.get("is_highlighted", False),
        features=dict(entry.get("features", {})),
    )


def get_plan(key: str) -> Plan | None:
    """Return the plan with `key`, or None if not registered."""
    for entry in settings.BILLING_PLANS:
        if entry.get("key") == key:
            return _normalize(entry)
    return None


def get_plans() -> list[Plan]:
    """Return all plans in declaration order."""
    return [_normalize(e) for e in settings.BILLING_PLANS]


def get_default_plan() -> Plan | None:
    """Plan marked is_default, else first free plan, else None."""
    for entry in settings.BILLING_PLANS:
        if entry.get("is_default"):
            return _normalize(entry)
    for entry in settings.BILLING_PLANS:
        if entry.get("is_free"):
            return _normalize(entry)
    return None


def get_free_plan() -> Plan | None:
    for entry in settings.BILLING_PLANS:
        if entry.get("is_free"):
            return _normalize(entry)
    return None


def price_id_for(plan: Plan, billing_cycle: str) -> str:
    """
    Return the Stripe price ID for the given billing cycle.

    Raises ValueError if the plan has no price ID for the requested cycle.
    """
    if billing_cycle == "monthly":
        price_id = plan.monthly_price_id
    elif billing_cycle == "annual":
        price_id = plan.annual_price_id
    else:
        raise ValueError(f"Unknown billing cycle: {billing_cycle}")
    if not price_id:
        raise ValueError(f"Plan {plan.key!r} has no Stripe price ID for {billing_cycle} billing.")
    return price_id


def resolve_plan_by_price_id(price_id: str) -> Plan | None:
    """Return the plan whose monthly_price_id or annual_price_id matches."""
    if not price_id:
        return None
    for entry in settings.BILLING_PLANS:
        if entry.get("monthly_price_id") == price_id or entry.get("annual_price_id") == price_id:
            return _normalize(entry)
    return None
