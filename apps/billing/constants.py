from django.db import models


class SubscriptionStatus(models.TextChoices):
    """Mirrors Stripe's subscription status values."""

    TRIALING = "trialing", "Trialing"
    ACTIVE = "active", "Active"
    PAST_DUE = "past_due", "Past due"
    CANCELED = "canceled", "Canceled"
    INCOMPLETE = "incomplete", "Incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired", "Incomplete expired"
    UNPAID = "unpaid", "Unpaid"
    PAUSED = "paused", "Paused"


class BillingCycle(models.TextChoices):
    MONTHLY = "monthly", "Monthly"
    ANNUAL = "annual", "Annual"


ACTIVE_STATUSES = frozenset({SubscriptionStatus.TRIALING, SubscriptionStatus.ACTIVE})

# Stripe API version pin. Bumping this is a coordinated change: re-test the
# webhook payload shape (period fields moved to item level in 2024-10-28) and
# replay any saved fixtures.
STRIPE_API_VERSION = "2024-10-28.acacia"

# Cap on Stripe webhook retries. Stripe's default retry window is ~3 days with
# exponential backoff (roughly 5-7 attempts). After this many failures we keep
# the dedupe marker and return 200 so Stripe stops retrying a deterministic bug.
WEBHOOK_MAX_FAILURES = 5
