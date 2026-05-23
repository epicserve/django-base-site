"""
Example BILLING_PLANS factory + BILLING_FEATURES catalog (opt-in via BILLING_USE_EXAMPLE_PLANS).

Lets the template maintainer (and downstream users kicking the tires)
test the billing UX without editing `config/settings/_base.py`. Enable
in `.env` with:

    BILLING_ENABLED=true
    BILLING_USE_EXAMPLE_PLANS=true
    STRIPE_PRICE_PRO_MONTHLY=price_...
    STRIPE_PRICE_PRO_ANNUAL=price_...
    STRIPE_PRICE_BUSINESS_MONTHLY=price_...
    STRIPE_PRICE_BUSINESS_ANNUAL=price_...

`config/settings/_base.py` calls `build_plans({...})` and passes the four
Stripe price IDs (read via the project's standard `env()` helper). Reading
env vars in this module directly via `os.environ` doesn't work because
`epicenv` loads `.env` into its own value store, not `os.environ`.

See `apps.billing.plans` and `apps.billing.features` for the schema.
"""


def build_plans(price_ids: dict[str, str]) -> list[dict]:
    """
    Return the example BILLING_PLANS list with Stripe price IDs injected.

    `price_ids` keys map to plan key + cycle, e.g. `"pro_monthly"`,
    `"pro_annual"`, `"business_monthly"`, `"business_annual"`. Missing keys
    default to "" — fine for the seed command, which only needs amounts to
    create prices in Stripe, but `BillingConfig.ready()` will refuse to boot
    if `BILLING_ENABLED=true` with empty price IDs.
    """
    return [
        {
            "key": "free",
            "name": "Free",
            "description": "For personal projects and trying things out.",
            "is_free": True,
            "is_default": True,
            "features": {
                "teams": False,
                "max_team_count": 0,
                "advanced_reporting": False,
            },
        },
        {
            "key": "pro",
            "name": "Pro",
            "description": "For growing teams that need collaboration.",
            "monthly_price_id": price_ids.get("pro_monthly", ""),
            "annual_price_id": price_ids.get("pro_annual", ""),
            "monthly_price_cents": 1900,
            "annual_price_cents": 19000,  # ~2 months free vs. monthly
            "currency": "usd",
            "trial_days": 14,
            "seat_based": True,
            "is_highlighted": True,
            "features": {
                "teams": True,
                "max_team_count": 10,
                "advanced_reporting": False,
            },
        },
        {
            "key": "business",
            "name": "Business",
            "description": "Advanced reporting and unlimited teams.",
            "monthly_price_id": price_ids.get("business_monthly", ""),
            "annual_price_id": price_ids.get("business_annual", ""),
            "monthly_price_cents": 4900,
            "annual_price_cents": 49000,
            "currency": "usd",
            "trial_days": 14,
            "seat_based": True,
            "features": {
                "teams": True,
                "max_team_count": 100,
                "advanced_reporting": True,
            },
        },
    ]


BILLING_FEATURES: list[dict] = [
    {
        "key": "teams",
        "label": "Teams",
        "description": "Group org members into teams.",
        "type": "bool",
        "default": True,  # unrestricted when billing is off
    },
    {
        "key": "max_team_count",
        "label": "Team count",
        "description": "Maximum number of teams.",
        "type": "limit",
        "default": 0,
    },
    {
        "key": "advanced_reporting",
        "label": "Advanced reporting",
        "description": "PDF exports and scheduled reports.",
        "type": "bool",
        "default": False,
    },
]
