import pytest
from model_bakery import baker

from apps.billing.access import org_feature_value, org_has_feature
from apps.billing.constants import SubscriptionStatus
from apps.billing.models import Subscription

PLANS = [
    {
        "key": "free",
        "name": "Free",
        "is_free": True,
        "is_default": True,
        "features": {"max_team_count": 1, "advanced_reporting": False},
    },
    {
        "key": "pro",
        "name": "Pro",
        "monthly_price_id": "price_pro_monthly",
        "features": {"max_team_count": 10, "advanced_reporting": True},
    },
]
FEATURES = [
    {"key": "max_team_count", "label": "Teams", "type": "limit", "default": 0},
    {"key": "advanced_reporting", "label": "Reporting", "type": "bool", "default": False},
]


@pytest.fixture
def billing_settings(settings):
    settings.BILLING_ENABLED = True
    settings.BILLING_PLANS = PLANS
    settings.BILLING_FEATURES = FEATURES
    return settings


@pytest.mark.django_db
class TestOrgFeatureValue:
    def test_disabled_returns_feature_default(self, settings):
        settings.BILLING_ENABLED = False
        settings.BILLING_PLANS = PLANS
        settings.BILLING_FEATURES = FEATURES
        org = baker.make("organizations.Organization")
        assert org_feature_value(org, "max_team_count") == 0
        assert org_feature_value(org, "advanced_reporting") is False

    def test_no_sub_uses_default_plan(self, billing_settings):
        org = baker.make("organizations.Organization")
        assert org_feature_value(org, "max_team_count") == 1
        assert org_feature_value(org, "advanced_reporting") is False

    def test_active_sub_uses_plan_features(self, billing_settings):
        org = baker.make("organizations.Organization")
        Subscription.objects.create(
            organization=org,
            stripe_subscription_id="sub_1",
            plan_key="pro",
            status=SubscriptionStatus.ACTIVE,
        )
        assert org_feature_value(org, "max_team_count") == 10
        assert org_feature_value(org, "advanced_reporting") is True

    def test_past_due_falls_back_to_default_plan(self, billing_settings):
        org = baker.make("organizations.Organization")
        Subscription.objects.create(
            organization=org,
            stripe_subscription_id="sub_2",
            plan_key="pro",
            status=SubscriptionStatus.PAST_DUE,
        )
        assert org_feature_value(org, "max_team_count") == 1
        assert org_feature_value(org, "advanced_reporting") is False

    def test_unknown_plan_key_falls_back_to_default(self, billing_settings):
        org = baker.make("organizations.Organization")
        Subscription.objects.create(
            organization=org,
            stripe_subscription_id="sub_3",
            plan_key="ghost",
            status=SubscriptionStatus.ACTIVE,
        )
        assert org_feature_value(org, "max_team_count") == 1


@pytest.mark.django_db
class TestOrgHasFeature:
    def test_bool_feature(self, billing_settings):
        org = baker.make("organizations.Organization")
        Subscription.objects.create(
            organization=org,
            stripe_subscription_id="sub_a",
            plan_key="pro",
            status=SubscriptionStatus.ACTIVE,
        )
        assert org_has_feature(org, "advanced_reporting") is True

    def test_limit_feature_zero_is_false(self, settings):
        settings.BILLING_ENABLED = True
        settings.BILLING_FEATURES = FEATURES
        settings.BILLING_PLANS = [{"key": "f", "name": "F", "is_free": True, "is_default": True, "features": {}}]
        org = baker.make("organizations.Organization")
        assert org_has_feature(org, "max_team_count") is False

    def test_disabled_passes_when_default_truthy(self, settings):
        settings.BILLING_ENABLED = False
        settings.BILLING_FEATURES = [{"key": "x", "label": "X", "type": "bool", "default": True}]
        org = baker.make("organizations.Organization")
        assert org_has_feature(org, "x") is True
