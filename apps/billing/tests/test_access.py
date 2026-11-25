from django.test import override_settings

from apps.base.tests import BaseTest
from apps.billing.access import org_feature_value, org_has_feature
from apps.billing.constants import SubscriptionStatus
from apps.billing.tests.recipes import BILLING_SETTINGS, make_subscription
from apps.organizations.tests.recipes import make_org


@override_settings(**BILLING_SETTINGS)
class TestOrgFeatureValue(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.org = make_org()

    def test_disabled_returns_feature_default(self):
        with self.settings(BILLING_ENABLED=False):
            assert org_feature_value(self.org, "max_team_count") == 0
            assert org_feature_value(self.org, "advanced_reporting") is False

    def test_no_sub_uses_default_plan(self):
        assert org_feature_value(self.org, "max_team_count") == 1
        assert org_feature_value(self.org, "advanced_reporting") is False

    def test_active_sub_uses_plan_features(self):
        make_subscription(self.org, plan_key="pro", status=SubscriptionStatus.ACTIVE)

        assert org_feature_value(self.org, "max_team_count") == 10
        assert org_feature_value(self.org, "advanced_reporting") is True

    def test_past_due_falls_back_to_default_plan(self):
        make_subscription(self.org, plan_key="pro", status=SubscriptionStatus.PAST_DUE)

        assert org_feature_value(self.org, "max_team_count") == 1
        assert org_feature_value(self.org, "advanced_reporting") is False

    def test_unknown_plan_key_falls_back_to_default(self):
        make_subscription(self.org, plan_key="ghost", status=SubscriptionStatus.ACTIVE)

        assert org_feature_value(self.org, "max_team_count") == 1


@override_settings(**BILLING_SETTINGS)
class TestOrgHasFeature(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.org = make_org()

    def test_bool_feature(self):
        make_subscription(self.org, plan_key="pro", status=SubscriptionStatus.ACTIVE)

        assert org_has_feature(self.org, "advanced_reporting") is True

    def test_limit_feature_zero_is_false(self):
        # A default plan that doesn't set the limit leaves it at the feature's default of 0.
        with self.settings(
            BILLING_PLANS=[{"key": "f", "name": "F", "is_free": True, "is_default": True, "features": {}}]
        ):
            assert org_has_feature(self.org, "max_team_count") is False

    def test_disabled_passes_when_default_truthy(self):
        with self.settings(
            BILLING_ENABLED=False, BILLING_FEATURES=[{"key": "x", "label": "X", "type": "bool", "default": True}]
        ):
            assert org_has_feature(self.org, "x") is True
