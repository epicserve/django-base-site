from apps.billing.features import get_feature, get_features

FEATURES = [
    {"key": "teams", "label": "Teams", "type": "bool", "default": False},
    {"key": "max_team_count", "label": "Team count", "type": "limit", "default": 1},
]


class TestFeatureRegistry:
    def test_get_feature(self, settings):
        settings.BILLING_FEATURES = FEATURES
        f = get_feature("teams")
        assert f.key == "teams"
        assert f.type == "bool"
        assert f.default is False

    def test_get_feature_missing(self, settings):
        settings.BILLING_FEATURES = FEATURES
        assert get_feature("ghost") is None

    def test_get_features(self, settings):
        settings.BILLING_FEATURES = FEATURES
        keys = [f.key for f in get_features()]
        assert keys == ["teams", "max_team_count"]

    def test_default_type_is_bool(self, settings):
        settings.BILLING_FEATURES = [{"key": "x", "label": "X", "default": True}]
        f = get_feature("x")
        assert f.type == "bool"
