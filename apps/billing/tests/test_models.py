import pytest
from model_bakery import baker

from apps.billing.constants import SubscriptionStatus
from apps.billing.models import BillingCustomer, Subscription


@pytest.mark.django_db
class TestBillingCustomer:
    def test_str(self):
        org = baker.make("organizations.Organization", name="Acme")
        customer = BillingCustomer.objects.create(organization=org, stripe_customer_id="cus_123")
        assert "Acme" in str(customer)
        assert "cus_123" in str(customer)

    def test_one_to_one_with_organization(self):
        org = baker.make("organizations.Organization")
        BillingCustomer.objects.create(organization=org, stripe_customer_id="cus_abc")
        # Reverse accessor.
        assert org.billing_customer.stripe_customer_id == "cus_abc"


@pytest.mark.django_db
class TestSubscription:
    def test_is_active_for_trialing_and_active(self):
        org = baker.make("organizations.Organization")
        sub = Subscription.objects.create(
            organization=org,
            stripe_subscription_id="sub_1",
            plan_key="pro",
            status=SubscriptionStatus.TRIALING,
        )
        assert sub.is_active is True

        sub.status = SubscriptionStatus.ACTIVE
        assert sub.is_active is True

    def test_is_active_false_for_past_due(self):
        org = baker.make("organizations.Organization")
        sub = Subscription.objects.create(
            organization=org,
            stripe_subscription_id="sub_2",
            plan_key="pro",
            status=SubscriptionStatus.PAST_DUE,
        )
        assert sub.is_active is False

    def test_is_active_false_for_canceled(self):
        org = baker.make("organizations.Organization")
        sub = Subscription.objects.create(
            organization=org,
            stripe_subscription_id="sub_3",
            plan_key="pro",
            status=SubscriptionStatus.CANCELED,
        )
        assert sub.is_active is False
