from django.db import models

from apps.base.mixins import TimeStampModelMixin
from apps.billing.constants import ACTIVE_STATUSES, BillingCycle, SubscriptionStatus


class BillingCustomer(TimeStampModelMixin):
    """
    A Stripe customer attached to an Organization.

    Survives subscription cancellation so a resubscribing org reuses the same
    Stripe customer (and its saved payment methods).
    """

    organization = models.OneToOneField(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="billing_customer",
    )
    stripe_customer_id = models.CharField(max_length=64, unique=True, db_index=True)
    email = models.EmailField(blank=True, help_text="Mirror of the email Stripe knows for this customer.")

    def __str__(self):
        """Return a string representation of the customer."""
        return f"{self.organization.name} ({self.stripe_customer_id})"


class Subscription(TimeStampModelMixin):
    """
    Local mirror of the active Stripe subscription for an Organization.

    Stripe is the source of truth; this model stores the minimum needed to
    gate features and render the billing UI without round-tripping to Stripe
    on every request. The `raw` JSONField holds the last full Stripe payload
    for forensics — never read by app code.
    """

    organization = models.OneToOneField(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="subscription",
    )
    stripe_subscription_id = models.CharField(max_length=64, unique=True, db_index=True)
    plan_key = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Matches BILLING_PLANS[*]['key']. Falls back gracefully if removed.",
    )
    billing_cycle = models.CharField(max_length=16, choices=BillingCycle.choices, default=BillingCycle.MONTHLY)
    status = models.CharField(max_length=32, choices=SubscriptionStatus.choices, db_index=True)
    quantity = models.PositiveIntegerField(default=1, help_text="Seat count for seat-based plans; 1 otherwise.")
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True, db_index=True)
    trial_end = models.DateTimeField(null=True, blank=True, db_index=True)
    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)
    trial_ending_notified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Set once the trial-ending notification has fired (idempotency guard).",
    )
    raw = models.JSONField(default=dict, blank=True, help_text="Last full Stripe payload — forensics only.")

    class Meta:
        indexes = [
            models.Index(fields=["status", "current_period_end"]),
            models.Index(fields=["status", "trial_end"]),
        ]

    def __str__(self):
        """Return a string representation of the subscription."""
        return f"{self.organization.name} / {self.plan_key} ({self.status})"

    @property
    def is_active(self) -> bool:
        """Status that should grant feature access."""
        return self.status in ACTIVE_STATUSES


class WebhookEvent(TimeStampModelMixin):
    """
    Idempotency record for Stripe webhook deliveries.

    Stripe retries failed webhooks with the same event ID. The handler tries
    to insert a row keyed on `stripe_event_id`; on IntegrityError it returns
    200 immediately (already processed).
    """

    stripe_event_id = models.CharField(max_length=64, unique=True, db_index=True)
    event_type = models.CharField(max_length=64)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        """Return a string representation of the webhook event."""
        return f"{self.event_type} ({self.stripe_event_id})"
