from datetime import datetime
from typing import Any, Literal

from ninja import Schema


class FeatureOut(Schema):
    key: str
    label: str
    description: str = ""
    type: str = "bool"
    default: Any = None


class PlanOut(Schema):
    key: str
    name: str
    description: str = ""
    monthly_price_id: str = ""
    annual_price_id: str = ""
    monthly_price_cents: int = 0
    annual_price_cents: int = 0
    currency: str = "usd"
    trial_days: int = 0
    seat_based: bool = False
    is_free: bool = False
    is_default: bool = False
    is_highlighted: bool = False
    features: dict[str, Any] = {}


class PlanSummaryOut(Schema):
    key: str
    name: str


class SubscriptionOut(Schema):
    plan: PlanSummaryOut | None = None
    plan_key: str | None = None
    status: str | None = None
    billing_cycle: str | None = None
    quantity: int = 1
    current_period_end: datetime | None = None
    trial_end: datetime | None = None
    cancel_at_period_end: bool = False


class CheckoutIn(Schema):
    plan_key: str
    billing_cycle: Literal["monthly", "annual"]


class CheckoutOut(Schema):
    checkout_url: str


class PortalOut(Schema):
    portal_url: str
