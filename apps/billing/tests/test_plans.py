import pytest

from apps.billing.plans import (
    get_default_plan,
    get_free_plan,
    get_plan,
    get_plans,
    price_id_for,
    resolve_plan_by_price_id,
)

PLAN_FREE = {"key": "free", "name": "Free", "is_free": True, "is_default": True}
PLAN_PRO = {
    "key": "pro",
    "name": "Pro",
    "monthly_price_id": "price_pro_monthly",
    "annual_price_id": "price_pro_annual",
    "trial_days": 14,
    "seat_based": True,
    "features": {"max_team_count": 10, "advanced_reporting": True},
}


class TestPlanRegistry:
    def test_get_plan_returns_normalized_dataclass(self, settings):
        settings.BILLING_PLANS = [PLAN_FREE, PLAN_PRO]
        plan = get_plan("pro")
        assert plan is not None
        assert plan.key == "pro"
        assert plan.trial_days == 14
        assert plan.seat_based is True
        assert plan.features == {"max_team_count": 10, "advanced_reporting": True}

    def test_get_plan_missing_returns_none(self, settings):
        settings.BILLING_PLANS = [PLAN_FREE]
        assert get_plan("does-not-exist") is None

    def test_get_plans_returns_all_in_order(self, settings):
        settings.BILLING_PLANS = [PLAN_FREE, PLAN_PRO]
        assert [p.key for p in get_plans()] == ["free", "pro"]

    def test_get_default_plan_prefers_is_default(self, settings):
        settings.BILLING_PLANS = [PLAN_PRO, PLAN_FREE]
        assert get_default_plan().key == "free"

    def test_get_default_plan_falls_back_to_first_free(self, settings):
        settings.BILLING_PLANS = [PLAN_PRO, dict(PLAN_FREE, is_default=False)]
        assert get_default_plan().key == "free"

    def test_get_default_plan_returns_none_when_empty(self, settings):
        settings.BILLING_PLANS = []
        assert get_default_plan() is None

    def test_get_free_plan(self, settings):
        settings.BILLING_PLANS = [PLAN_PRO, PLAN_FREE]
        assert get_free_plan().key == "free"

    def test_price_id_for_monthly(self, settings):
        settings.BILLING_PLANS = [PLAN_PRO]
        plan = get_plan("pro")
        assert price_id_for(plan, "monthly") == "price_pro_monthly"

    def test_price_id_for_annual(self, settings):
        settings.BILLING_PLANS = [PLAN_PRO]
        plan = get_plan("pro")
        assert price_id_for(plan, "annual") == "price_pro_annual"

    def test_price_id_for_unknown_cycle_raises(self, settings):
        settings.BILLING_PLANS = [PLAN_PRO]
        plan = get_plan("pro")
        with pytest.raises(ValueError, match="Unknown billing cycle"):
            price_id_for(plan, "weekly")

    def test_price_id_for_missing_price_raises(self, settings):
        settings.BILLING_PLANS = [{"key": "x", "name": "X"}]
        plan = get_plan("x")
        with pytest.raises(ValueError, match="no Stripe price ID"):
            price_id_for(plan, "monthly")

    def test_resolve_plan_by_price_id(self, settings):
        settings.BILLING_PLANS = [PLAN_FREE, PLAN_PRO]
        assert resolve_plan_by_price_id("price_pro_monthly").key == "pro"
        assert resolve_plan_by_price_id("price_pro_annual").key == "pro"
        assert resolve_plan_by_price_id("nope") is None
        assert resolve_plan_by_price_id("") is None
