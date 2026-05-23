"""
Pure service functions for the billing app.

Producers (the API, the webhook handler, the reconcile task, signals) call into
this module; nothing here imports views, templates, or request objects, so the
same code is callable from a Django shell, a celery task, or a test.

Stripe is the source of truth. Local writes happen via `sync_subscription_from_stripe`
which is called both from webhook handlers and the reconcile task — the same
upsert path keeps drift from creeping in.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC
from typing import Any

from django.conf import settings
from django.db import transaction

from apps.billing.constants import STRIPE_API_VERSION, BillingCycle, SubscriptionStatus
from apps.billing.models import BillingCustomer, Subscription
from apps.billing.plans import (
    Plan,
    get_plan,
    price_id_for,
    resolve_plan_by_price_id,
)

logger = logging.getLogger(__name__)


def _stripe():
    """
    Return the configured stripe module.

    Raises RuntimeError if BILLING_ENABLED is False so accidental calls fail
    loudly instead of hitting the Stripe API with a blank key.
    """
    if not getattr(settings, "BILLING_ENABLED", False):
        raise RuntimeError("BILLING_ENABLED is False; billing services are not available.")

    import stripe

    if not stripe.api_key:
        stripe.api_key = settings.STRIPE_SECRET_KEY
    if getattr(stripe, "api_version", None) != STRIPE_API_VERSION:
        stripe.api_version = STRIPE_API_VERSION
    return stripe


def _seat_count_for(org) -> int:
    from apps.organizations.models import OrganizationMember

    # `or 1` guards checkout when the buyer hasn't been added to the org as a
    # member yet — Stripe rejects quantity=0 on a seat-based plan. Steady-state
    # the creator is always a member, so the fallback is only hit during the
    # creation race window.
    return OrganizationMember.objects.filter(organization=org).count() or 1


def _from_unix(value: int | None):
    if not value:
        return None
    from datetime import datetime

    return datetime.fromtimestamp(value, tz=UTC)


def get_or_create_customer(org, *, fallback_email: str = "") -> BillingCustomer:
    """
    Idempotent. Caches Stripe customer creation in BillingCustomer.

    `fallback_email` is used when `org.billing_email` is blank — typically the
    current user's email — so Stripe Checkout doesn't have to prompt the buyer
    for an address it could already infer. If an existing customer's email
    differs from the desired one, both Stripe and the local mirror are updated.
    """
    email = org.billing_email or fallback_email or ""
    existing = BillingCustomer.objects.filter(organization=org).first()
    if existing is not None:
        if email and email != existing.email:
            stripe = _stripe()
            stripe.Customer.modify(existing.stripe_customer_id, email=email)
            existing.email = email
            existing.save(update_fields=["email", "modified"])
        return existing

    stripe = _stripe()
    # Hash the inputs into the key so re-creating a customer with different
    # params (e.g. a now-known email) doesn't collide with the prior 24-hour
    # idempotency window.
    seed = f"{org.pk}|{org.slug}|{org.name}|{email}"
    key_hash = hashlib.sha256(seed.encode()).hexdigest()[:16]
    customer = stripe.Customer.create(
        email=email or None,
        name=org.name,
        metadata={"organization_id": str(org.pk), "organization_slug": org.slug},
        idempotency_key=f"org-{org.pk}-customer-{key_hash}",
    )
    return BillingCustomer.objects.create(
        organization=org,
        stripe_customer_id=customer.id,
        email=email,
    )


def create_checkout_session(
    org,
    *,
    plan_key: str,
    billing_cycle: str,
    success_url: str,
    cancel_url: str,
    user=None,
) -> str:
    """Return a Stripe Checkout URL for a new subscription."""
    plan = get_plan(plan_key)
    if plan is None:
        raise ValueError(f"Unknown plan key: {plan_key}")
    if plan.is_free:
        raise ValueError(f"Plan {plan_key!r} is the free tier and doesn't require checkout.")

    stripe = _stripe()
    fallback_email = getattr(user, "email", "") or ""
    customer = get_or_create_customer(org, fallback_email=fallback_email)
    price_id = price_id_for(plan, billing_cycle)
    quantity = _seat_count_for(org) if plan.seat_based else 1

    subscription_data: dict[str, Any] = {}
    if plan.trial_days and not Subscription.objects.filter(organization=org).exists():
        subscription_data["trial_period_days"] = plan.trial_days

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer.stripe_customer_id,
        line_items=[{"price": price_id, "quantity": quantity}],
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=str(org.pk),
        allow_promotion_codes=True,
        subscription_data=subscription_data or None,
        metadata={
            "organization_id": str(org.pk),
            "plan_key": plan.key,
            "billing_cycle": billing_cycle,
        },
        idempotency_key=(
            f"org-{org.pk}-checkout-{plan.key}-{billing_cycle}-"
            f"{hashlib.sha256(f'{customer.stripe_customer_id}|{price_id}|{quantity}'.encode()).hexdigest()[:16]}"
        ),
    )
    return session.url


def create_portal_session(org, *, return_url: str) -> str:
    """Return a Stripe Customer Portal URL."""
    customer = BillingCustomer.objects.filter(organization=org).first()
    if customer is None:
        raise ValueError("Organization has no Stripe customer; start a checkout first.")

    stripe = _stripe()
    session = stripe.billing_portal.Session.create(
        customer=customer.stripe_customer_id,
        return_url=return_url,
    )
    return session.url


def _resolve_plan_and_cycle(stripe_subscription) -> tuple[Plan | None, str]:
    """Inspect the first line item's price to pick a plan + billing cycle."""
    items = stripe_subscription.get("items", {}).get("data", [])
    if not items:
        return None, BillingCycle.MONTHLY
    price = items[0].get("price") or {}
    price_id = price.get("id", "")
    plan = resolve_plan_by_price_id(price_id)
    if plan is None:
        return None, BillingCycle.MONTHLY
    cycle = BillingCycle.ANNUAL if price_id == plan.annual_price_id else BillingCycle.MONTHLY
    return plan, cycle


def sync_subscription_from_stripe(stripe_subscription) -> Subscription | None:
    """Upsert the local Subscription row from a Stripe subscription payload."""
    customer_id = stripe_subscription.get("customer")
    if not customer_id:
        return None
    customer = BillingCustomer.objects.filter(stripe_customer_id=customer_id).first()
    if customer is None:
        # Subscription created in Stripe Dashboard for an unknown customer; skip.
        logger.warning(
            "Stripe subscription %s for unknown customer %s; skipping.", stripe_subscription.get("id"), customer_id
        )
        return None

    plan, cycle = _resolve_plan_and_cycle(stripe_subscription)
    plan_key = plan.key if plan is not None else (stripe_subscription.get("metadata") or {}).get("plan_key", "")
    if not plan_key:
        from apps.billing.plans import get_default_plan

        default = get_default_plan()
        plan_key = default.key if default is not None else "unknown"
        logger.warning(
            "Stripe subscription %s has no recognizable plan; falling back to %s.",
            stripe_subscription.get("id"),
            plan_key,
        )

    items = stripe_subscription.get("items", {}).get("data", [])
    quantity = items[0].get("quantity", 1) if items else 1
    period_start = _from_unix(stripe_subscription.get("current_period_start"))
    period_end = _from_unix(stripe_subscription.get("current_period_end"))
    if items and not period_start:
        period_start = _from_unix(items[0].get("current_period_start"))
    if items and not period_end:
        period_end = _from_unix(items[0].get("current_period_end"))

    raw_status = stripe_subscription.get("status", "")
    try:
        status = SubscriptionStatus(raw_status)
    except ValueError:
        logger.warning("Stripe subscription %s has unknown status %r.", stripe_subscription.get("id"), raw_status)
        status = SubscriptionStatus.INCOMPLETE

    defaults = {
        "stripe_subscription_id": stripe_subscription["id"],
        "plan_key": plan_key,
        "billing_cycle": cycle,
        "status": status,
        "quantity": quantity,
        "current_period_start": period_start,
        "current_period_end": period_end,
        "trial_end": _from_unix(stripe_subscription.get("trial_end")),
        "cancel_at_period_end": bool(stripe_subscription.get("cancel_at_period_end")),
        "canceled_at": _from_unix(stripe_subscription.get("canceled_at")),
        "raw": dict(stripe_subscription),
    }

    sub, _created = Subscription.objects.update_or_create(
        organization=customer.organization,
        defaults=defaults,
    )
    return sub


def sync_seat_quantity_by_id(org_id: int) -> None:
    """Recompute seat count for an org and update Stripe quantity if changed."""
    if not getattr(settings, "BILLING_ENABLED", False):
        return

    sub = Subscription.objects.filter(organization_id=org_id).first()
    if sub is None or sub.status not in {
        SubscriptionStatus.TRIALING,
        SubscriptionStatus.ACTIVE,
        SubscriptionStatus.PAST_DUE,
    }:
        return

    plan = get_plan(sub.plan_key)
    if plan is None or not plan.seat_based:
        return

    from apps.organizations.models import OrganizationMember

    new_qty = OrganizationMember.objects.filter(organization_id=org_id).count() or 1
    if new_qty == sub.quantity:
        return

    stripe = _stripe()
    stripe_sub = stripe.Subscription.retrieve(sub.stripe_subscription_id)
    items = stripe_sub.get("items", {}).get("data", [])
    if not items:
        return
    item_id = items[0].get("id")
    stripe.Subscription.modify(
        sub.stripe_subscription_id,
        items=[{"id": item_id, "quantity": new_qty}],
        proration_behavior="create_prorations",
    )
    sub.quantity = new_qty
    sub.save(update_fields=["quantity", "modified"])


def sync_seat_quantity(org) -> None:
    """Public entry point — defers to the by-id variant."""
    sync_seat_quantity_by_id(org.pk)


def sync_customer_email_by_id(org_id: int) -> None:
    """Push the org's billing_email to Stripe and the local mirror when it differs."""
    if not getattr(settings, "BILLING_ENABLED", False):
        return

    customer = BillingCustomer.objects.filter(organization_id=org_id).first()
    if customer is None:
        return

    from apps.organizations.models import Organization

    org = Organization.objects.filter(pk=org_id).only("billing_email").first()
    if org is None:
        return

    desired = org.billing_email or ""
    # Don't blank out Stripe when the field is cleared — receipts should still
    # have somewhere to land. Only push positive changes.
    if not desired or desired == customer.email:
        return

    stripe = _stripe()
    stripe.Customer.modify(customer.stripe_customer_id, email=desired)
    customer.email = desired
    customer.save(update_fields=["email", "modified"])


def schedule_seat_sync(org) -> None:
    """Defer a seat sync to after the current DB transaction commits."""
    transaction.on_commit(lambda: sync_seat_quantity_by_id(org.pk))
