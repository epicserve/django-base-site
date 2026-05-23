"""
Stripe webhook handler.

Mounted at `/webhooks/stripe/` (see config/urls.py) only when
BILLING_ENABLED=True. Lives outside the `/api/` ninja router because Stripe
posts unauthenticated requests with HMAC signatures, not session+CSRF auth.

Idempotency: Stripe retries failed webhook deliveries with the same event ID.
The handler tries to insert a `WebhookEvent(stripe_event_id=...)` row; on
IntegrityError, if the existing row is already processed (or has reached
WEBHOOK_MAX_FAILURES) we return 200 immediately. On handler exception we bump
`failure_count` on the row (rather than deleting it) and 500 — so Stripe
retries with backoff but a deterministic bug stops after MAX failures.
Unhandled event types return 200 so Stripe stops retrying.
"""

from __future__ import annotations

import logging

from django.db import IntegrityError, transaction
from django.db.models import F
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.billing.constants import WEBHOOK_MAX_FAILURES, SubscriptionStatus
from apps.billing.models import BillingCustomer, Subscription, WebhookEvent
from apps.billing.services import _stripe, sync_subscription_from_stripe

logger = logging.getLogger(__name__)


def _on_checkout_completed(event):
    obj = event["data"]["object"]
    org_pk = obj.get("client_reference_id")
    sub_id = obj.get("subscription")
    if not sub_id:
        return
    stripe = _stripe()
    stripe_sub = stripe.Subscription.retrieve(sub_id)
    sub = sync_subscription_from_stripe(stripe_sub)
    if sub is not None and org_pk:
        from apps.notifications.services import notify

        owners = list(sub.organization.owners)
        if owners:
            notify(
                owners,
                title="Subscription activated",
                body=f"Your {sub.organization.name} subscription is active.",
                url=f"/organizations/{sub.organization.slug}/settings/billing/",
                organization=sub.organization,
                category="billing_subscription_activated",
                target=sub,
            )


def _on_subscription_changed(event):
    sync_subscription_from_stripe(event["data"]["object"])


def _on_subscription_deleted(event):
    obj = event["data"]["object"]
    sub = Subscription.objects.filter(stripe_subscription_id=obj["id"]).first()
    if sub is None:
        return
    sub.status = SubscriptionStatus.CANCELED
    sub.canceled_at = timezone.now()
    sub.save(update_fields=["status", "canceled_at", "modified"])

    from apps.base.utils.email import send_email
    from apps.notifications.services import notify

    owners = list(sub.organization.owners)
    if owners:
        notify(
            owners,
            title="Subscription canceled",
            body=f"Your {sub.organization.name} subscription has been canceled.",
            url=f"/organizations/{sub.organization.slug}/settings/billing/",
            organization=sub.organization,
            category="billing_subscription_canceled",
            target=sub,
        )
        send_email(
            sending_user=None,
            recipients=owners,
            subject=f"Your {sub.organization.name} subscription has been canceled",
            base_template_name="billing/emails/subscription_canceled",
            context={"subscription": sub, "organization": sub.organization},
            category="billing_subscription_canceled",
        )


def _on_payment_succeeded(event):
    # The customer.subscription.updated event already covers period bumps.
    return


def _on_payment_failed(event):
    obj = event["data"]["object"]
    customer_id = obj.get("customer")
    customer = BillingCustomer.objects.filter(stripe_customer_id=customer_id).first()
    if customer is None:
        return

    from apps.base.utils.email import send_email
    from apps.notifications.services import notify

    org = customer.organization
    owners = list(org.owners)
    if not owners:
        return
    notify(
        owners,
        title="Payment failed",
        body=f"Your last payment for {org.name} could not be processed.",
        url=f"/organizations/{org.slug}/settings/billing/",
        organization=org,
        category="billing_payment_failed",
    )
    send_email(
        sending_user=None,
        recipients=owners,
        subject=f"Payment failed for {org.name}",
        base_template_name="billing/emails/payment_failed",
        context={"organization": org, "amount_due": obj.get("amount_due", 0)},
        category="billing_payment_failed",
    )


_EVENT_HANDLERS = {
    "checkout.session.completed": _on_checkout_completed,
    "customer.subscription.created": _on_subscription_changed,
    "customer.subscription.updated": _on_subscription_changed,
    "customer.subscription.deleted": _on_subscription_deleted,
    "invoice.payment_succeeded": _on_payment_succeeded,
    "invoice.payment_failed": _on_payment_failed,
}


@csrf_exempt
@require_POST
def stripe_webhook(request: HttpRequest) -> HttpResponse:
    from django.conf import settings

    import stripe

    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponseBadRequest("invalid signature")

    event_id = event["id"]
    event_type = event["type"]

    # Idempotency + bounded retry. We keep the WebhookEvent row across failures
    # (instead of deleting on exception) so a deterministic handler bug doesn't
    # cause Stripe to retry forever — past WEBHOOK_MAX_FAILURES we return 200
    # and operators see the failed row in admin.
    try:
        with transaction.atomic():
            record = WebhookEvent.objects.create(stripe_event_id=event_id, event_type=event_type)
    except IntegrityError:
        record = WebhookEvent.objects.get(stripe_event_id=event_id)
        if record.processed_at is not None:
            return HttpResponse(status=200)
        if record.failure_count >= WEBHOOK_MAX_FAILURES:
            logger.warning(
                "Stripe webhook %s (%s) gave up after %d failures.",
                event_id,
                event_type,
                record.failure_count,
            )
            return HttpResponse(status=200)

    handler = _EVENT_HANDLERS.get(event_type)
    if handler is None:
        # Unknown event type — 200 so Stripe stops retrying.
        WebhookEvent.objects.filter(pk=record.pk).update(processed_at=timezone.now())
        return HttpResponse(status=200)

    try:
        handler(event)
    except Exception as exc:
        logger.exception("Stripe webhook handler failed for event %s (%s)", event_id, event_type)
        WebhookEvent.objects.filter(pk=record.pk).update(
            failure_count=F("failure_count") + 1,
            last_error=str(exc)[:1000],
        )
        record.refresh_from_db(fields=["failure_count"])
        if record.failure_count >= WEBHOOK_MAX_FAILURES:
            return HttpResponse(status=200)
        return HttpResponse(status=500)

    WebhookEvent.objects.filter(pk=record.pk).update(processed_at=timezone.now())
    return HttpResponse(status=200)
