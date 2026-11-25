from apps.billing.features import get_feature, get_features
from apps.billing.tests.recipes import BILLING_FEATURES


class TestFeatureRegistry:
    def test_get_feature(self, settings):
        settings.BILLING_FEATURES = BILLING_FEATURES
        f = get_feature("advanced_reporting")
        assert f is not None
        assert f.key == "advanced_reporting"
        assert f.type == "bool"
        assert f.default is False

    def test_get_feature_missing(self, settings):
        settings.BILLING_FEATURES = BILLING_FEATURES
        assert get_feature("ghost") is None

    def test_get_features(self, settings):
        settings.BILLING_FEATURES = BILLING_FEATURES
        keys = [f.key for f in get_features()]
        assert keys == ["max_team_count", "advanced_reporting"]

    def test_default_type_is_bool(self, settings):
        settings.BILLING_FEATURES = [{"key": "x", "label": "X", "default": True}]
        f = get_feature("x")
        assert f is not None
        assert f.type == "bool"
