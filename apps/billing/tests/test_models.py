from apps.base.tests import BaseTest
from apps.billing.constants import SubscriptionStatus
from apps.billing.models import Subscription
from apps.billing.recipes import make_customer
from apps.organizations.models import Organization
from apps.organizations.recipes import make_org


class TestBillingCustomer(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.org = make_org(name="Acme")
        cls.customer = make_customer(cls.org, stripe_customer_id="cus_123")

    def test_str(self):
        assert "Acme" in str(self.customer)
        assert "cus_123" in str(self.customer)

    def test_one_to_one_with_organization(self):
        # Reverse accessor, read from the database rather than the cache `create()` filled in.
        assert Organization.objects.get(pk=self.org.pk).billing_customer.stripe_customer_id == "cus_123"


class TestSubscription:
    """`is_active` reads only `status`, so unsaved subscriptions do."""

    def test_is_active_for_trialing_and_active(self):
        sub = Subscription(plan_key="pro", status=SubscriptionStatus.TRIALING)
        assert sub.is_active is True

        sub.status = SubscriptionStatus.ACTIVE
        assert sub.is_active is True

    def test_is_active_false_for_past_due(self):
        assert Subscription(plan_key="pro", status=SubscriptionStatus.PAST_DUE).is_active is False

    def test_is_active_false_for_canceled(self):
        assert Subscription(plan_key="pro", status=SubscriptionStatus.CANCELED).is_active is False
