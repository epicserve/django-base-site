from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from celery import shared_task


@shared_task
def check_trials_ending() -> int:
    """
    Send 'trial ending' notification to org owners 3 days before trial_end.

    Idempotent via Subscription.trial_ending_notified_at; daily cron runs but
    re-sends are gated by that timestamp. No-ops when BILLING_ENABLED is False.
    """
    if not getattr(settings, "BILLING_ENABLED", False):
        return 0

    from apps.base.utils.email import send_email
    from apps.billing.constants import SubscriptionStatus
    from apps.billing.models import Subscription
    from apps.notifications.services import notify

    now = timezone.now()
    cutoff_low = now + timedelta(days=2, hours=12)
    cutoff_high = now + timedelta(days=3, hours=12)
    qs = Subscription.objects.filter(
        status=SubscriptionStatus.TRIALING,
        trial_end__gte=cutoff_low,
        trial_end__lte=cutoff_high,
        trial_ending_notified_at__isnull=True,
    )
    sent = 0
    for sub in qs:
        owners = list(sub.organization.owners)
        if owners:
            notify(
                owners,
                title="Your trial is ending soon",
                body=f"Your {sub.organization.name} trial ends on {sub.trial_end:%b %d, %Y}.",
                url=f"/organizations/{sub.organization.slug}/settings/billing/",
                organization=sub.organization,
                category="billing_trial_ending",
                target=sub,
            )
            send_email(
                sending_user=None,
                recipients=owners,
                subject=f"Your {sub.organization.name} trial is ending soon",
                base_template_name="billing/emails/trial_ending",
                context={"subscription": sub, "organization": sub.organization},
                category="billing_trial_ending",
            )
        sub.trial_ending_notified_at = now
        sub.save(update_fields=["trial_ending_notified_at", "modified"])
        sent += 1
    return sent


@shared_task
def reconcile_subscriptions() -> int:
    """
    Defensive sweep against missed Stripe webhooks.

    Iterates all BillingCustomer rows, fetches subs from Stripe, and re-runs
    `sync_subscription_from_stripe`. No-ops when BILLING_ENABLED is False.
    """
    if not getattr(settings, "BILLING_ENABLED", False):
        return 0

    from apps.billing.models import BillingCustomer
    from apps.billing.services import _stripe, sync_subscription_from_stripe

    stripe = _stripe()
    count = 0
    for customer in BillingCustomer.objects.iterator(chunk_size=100):
        subs = stripe.Subscription.list(customer=customer.stripe_customer_id, status="all", limit=100)
        for sub in subs.auto_paging_iter():
            sync_subscription_from_stripe(sub)
            count += 1
    return count
