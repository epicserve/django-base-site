"""
Tests for `sync_subscription_from_stripe`.

This is the upsert that both webhook handlers and the reconcile task funnel
through; Stripe is the source of truth, so the state transitions here are
the single most important contract in the billing module.
"""

from django.test import override_settings

from apps.base.tests import BaseTest
from apps.billing.constants import BillingCycle, SubscriptionStatus
from apps.billing.models import Subscription
from apps.billing.services import sync_subscription_from_stripe
from apps.billing.tests.recipes import BILLING_SETTINGS, make_customer, make_subscription
from apps.organizations.tests.recipes import make_org


def _payload(*, customer="cus_1", sub_id="sub_1", price_id="price_pro_monthly", status="active", quantity=3):
    """Build a Stripe-shaped subscription dict for the upsert."""
    return {
        "id": sub_id,
        "customer": customer,
        "status": status,
        "current_period_start": 1_700_000_000,
        "current_period_end": 1_702_000_000,
        "trial_end": None,
        "cancel_at_period_end": False,
        "canceled_at": None,
        "items": {
            "data": [
                {
                    "id": "si_1",
                    "quantity": quantity,
                    "price": {"id": price_id},
                    "current_period_start": 1_700_000_000,
                    "current_period_end": 1_702_000_000,
                }
            ]
        },
        "metadata": {},
    }


@override_settings(**BILLING_SETTINGS)
class TestSyncSubscriptionFromStripe(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.org = make_org()
        cls.customer = make_customer(cls.org)

    def test_creates_new_subscription(self):
        sub = sync_subscription_from_stripe(_payload(customer=self.customer.stripe_customer_id, sub_id="sub_new"))

        assert sub is not None
        assert sub.organization_id == self.org.pk
        assert sub.stripe_subscription_id == "sub_new"
        assert sub.plan_key == "pro"
        assert sub.billing_cycle == BillingCycle.MONTHLY
        assert sub.status == SubscriptionStatus.ACTIVE
        assert sub.quantity == 3

    def test_annual_price_id_sets_cycle_annual(self):
        sub = sync_subscription_from_stripe(
            _payload(customer=self.customer.stripe_customer_id, sub_id="sub_year", price_id="price_pro_annual")
        )

        assert sub is not None
        assert sub.billing_cycle == BillingCycle.ANNUAL

    def test_updates_existing_subscription(self):
        existing = make_subscription(self.org, plan_key="pro", status=SubscriptionStatus.TRIALING, quantity=1)

        sub = sync_subscription_from_stripe(
            _payload(
                customer=self.customer.stripe_customer_id,
                sub_id=existing.stripe_subscription_id,
                status="past_due",
                quantity=7,
            )
        )

        assert sub is not None
        assert sub.status == SubscriptionStatus.PAST_DUE
        assert sub.quantity == 7
        assert Subscription.objects.filter(organization=self.org).count() == 1

    def test_returns_none_for_unknown_customer(self):
        result = sync_subscription_from_stripe(_payload(customer="cus_orphan"))
        assert result is None
        assert Subscription.objects.count() == 0

    def test_returns_none_when_customer_missing(self):
        payload = _payload()
        del payload["customer"]
        assert sync_subscription_from_stripe(payload) is None

    def test_unknown_status_falls_back_to_incomplete(self):
        sub = sync_subscription_from_stripe(
            _payload(customer=self.customer.stripe_customer_id, sub_id="sub_status", status="weirdness")
        )

        assert sub is not None
        assert sub.status == SubscriptionStatus.INCOMPLETE

    def test_unknown_plan_falls_back_to_default_plan(self):
        sub = sync_subscription_from_stripe(
            _payload(customer=self.customer.stripe_customer_id, sub_id="sub_plan", price_id="price_unknown")
        )

        # Falls back to the default plan ("free") since no recognized price.
        assert sub is not None
        assert sub.plan_key == "free"
