from dataclasses import asdict

from django.conf import settings

from ninja import Router
from ninja.errors import HttpError

from apps.base.permissions import require_org_owner
from apps.billing.features import get_features
from apps.billing.models import Subscription
from apps.billing.plans import get_default_plan, get_plan, get_plans
from apps.billing.schemas import (
    CheckoutIn,
    CheckoutOut,
    FeatureOut,
    PlanOut,
    PortalOut,
    SubscriptionOut,
)
from apps.billing.services import create_checkout_session, create_portal_session

router = Router(tags=["billing"])


@router.get("/plans/", response=list[PlanOut], auth=None)
def list_plans(request):
    """Public — drives the marketing pricing page."""
    return [PlanOut(**asdict(p)) for p in get_plans()]


@router.get("/features/", response=list[FeatureOut], auth=None)
def list_features(request):
    """Public — used by pricing-page comparison tables."""
    return [FeatureOut(**asdict(f)) for f in get_features()]


@router.get("/subscription/", response=SubscriptionOut)
def get_subscription(request):
    """
    Owner-only. Returns the org's current subscription state.

    When the org has no Subscription row, returns the default-plan shape so
    the SPA renders a "pick a plan" UI off this endpoint instead of 404.
    """
    org = require_org_owner(request)
    sub = Subscription.objects.filter(organization=org).first()
    if sub is None:
        plan = get_default_plan()
        return SubscriptionOut(
            plan={"key": plan.key, "name": plan.name} if plan else None,
            plan_key=plan.key if plan else None,
            status=None,
            billing_cycle=None,
            quantity=1,
            current_period_end=None,
            trial_end=None,
            cancel_at_period_end=False,
        )
    plan = get_plan(sub.plan_key) or get_default_plan()
    return SubscriptionOut(
        plan={"key": plan.key, "name": plan.name} if plan else None,
        plan_key=sub.plan_key,
        status=sub.status,
        billing_cycle=sub.billing_cycle,
        quantity=sub.quantity,
        current_period_end=sub.current_period_end,
        trial_end=sub.trial_end,
        cancel_at_period_end=sub.cancel_at_period_end,
    )


@router.post("/checkout/", response=CheckoutOut)
def create_checkout(request, payload: CheckoutIn):
    org = require_org_owner(request)
    plan = get_plan(payload.plan_key)
    if plan is None:
        raise HttpError(404, f"Unknown plan: {payload.plan_key}")
    if plan.is_free:
        raise HttpError(400, "The free plan doesn't require checkout.")

    base = settings.SITE_URL.rstrip("/")
    success_url = f"{base}/organizations/{org.slug}/settings/billing/?checkout=success"
    cancel_url = f"{base}/pricing/"
    try:
        url = create_checkout_session(
            org,
            plan_key=payload.plan_key,
            billing_cycle=payload.billing_cycle,
            success_url=success_url,
            cancel_url=cancel_url,
        )
    except ValueError as exc:
        raise HttpError(400, str(exc)) from exc
    return CheckoutOut(checkout_url=url)


@router.post("/portal/", response=PortalOut)
def create_portal(request):
    org = require_org_owner(request)
    if not Subscription.objects.filter(organization=org).exists():
        raise HttpError(409, "No active subscription. Start a checkout first.")
    base = settings.SITE_URL.rstrip("/")
    return_url = f"{base}/organizations/{org.slug}/settings/billing/?portal=return"
    try:
        url = create_portal_session(org, return_url=return_url)
    except ValueError as exc:
        raise HttpError(400, str(exc)) from exc
    return PortalOut(portal_url=url)
