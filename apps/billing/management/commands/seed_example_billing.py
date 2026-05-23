"""
Create example Pro + Business products and prices in Stripe (idempotent).

Pairs with `BILLING_USE_EXAMPLE_PLANS=true` so a developer can dogfood the
billing UX with one command instead of clicking through the Stripe Dashboard.

Idempotency comes from Stripe's own `lookup_key` primitive on Price (unique
per account, strongly consistent). Each rerun does:

1. List prices by lookup_key (`djbs_example_<plan>_<cycle>`).
2. If any are found, derive the product from `price.product` and reuse it.
   Otherwise, create a fresh product (stamped with a `djbs_seed_key` metadata
   marker for human discoverability in the Stripe Dashboard) and attach the
   missing prices to it.

Rerunning the command never creates duplicate products or prices. (We avoid
`stripe.Product.search` because its search index has eventual consistency,
which produced duplicate products on rapid back-to-back runs.)
"""

import sys

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

import stripe

from apps.billing import example_plans
from apps.billing.constants import STRIPE_API_VERSION

SEED_KEY_PREFIX = "example"
LOOKUP_KEY_PREFIX = "djbs_example"
CYCLES = (("monthly", "month"), ("annual", "year"))


class Command(BaseCommand):
    help = "Create example Pro + Business products and prices in Stripe (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force-live",
            action="store_true",
            help="Allow running against a sk_live_… key. Off by default to prevent "
            "accidentally creating example products in a real Stripe account.",
        )

    def handle(self, *args, force_live: bool = False, **options):
        secret_key = settings.STRIPE_SECRET_KEY
        if not secret_key:
            raise CommandError(
                "Set STRIPE_SECRET_KEY in .env before running this command. Use a Stripe test-mode key (sk_test_…)."
            )
        if secret_key.startswith("sk_live_") and not force_live:
            raise CommandError(
                "Refusing to seed against a live Stripe account. "
                "Pass --force-live to override (you almost certainly don't want to)."
            )

        stripe.api_key = secret_key
        stripe.api_version = STRIPE_API_VERSION

        # The command creates the prices itself, so it doesn't care about price IDs.
        non_free = [p for p in example_plans.build_plans({}) if not p.get("is_free")]
        env_lines: list[str] = []

        for plan in non_free:
            prices_by_cycle = self._upsert_plan(plan)
            for cycle, _ in CYCLES:
                price = prices_by_cycle[cycle]
                env_lines.append(f"STRIPE_PRICE_{plan['key'].upper()}_{cycle.upper()}={price.id}")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Done. Paste these into your .env:"))
        self.stdout.write("")
        for line in env_lines:
            self.stdout.write(f"    {line}")
        self.stdout.write("")
        self.stdout.write("Then set BILLING_USE_EXAMPLE_PLANS=true and restart.")

    def _upsert_plan(self, plan: dict) -> dict[str, stripe.Price]:
        # Look up existing prices for both cycles first — they're the idempotency anchor.
        # Any existing price tells us which product to attach missing prices to, which
        # sidesteps `Product.search`'s eventual consistency.
        existing: dict[str, stripe.Price] = {}
        for cycle, _ in CYCLES:
            lookup_key = self._lookup_key(plan, cycle)
            result = stripe.Price.list(lookup_keys=[lookup_key], limit=1)
            if result.data:
                existing[cycle] = result.data[0]
                self.stdout.write(f"Reusing price {result.data[0].id} ({lookup_key}).")

        if existing:
            product_id = next(iter(existing.values())).product
            product = stripe.Product.retrieve(product_id)
            self.stdout.write(f"Reusing product {product.id} for {plan['key']!r}.")
        else:
            product = stripe.Product.create(
                name=plan["name"],
                description=plan.get("description", ""),
                metadata={
                    "djbs_seed_key": f"{SEED_KEY_PREFIX}_{plan['key']}",
                    "plan_key": plan["key"],
                },
            )
            self.stdout.write(self.style.SUCCESS(f"Created product {product.id} for {plan['key']!r}."))

        prices: dict[str, stripe.Price] = dict(existing)
        for cycle, interval in CYCLES:
            if cycle in prices:
                continue
            lookup_key = self._lookup_key(plan, cycle)
            price = stripe.Price.create(
                product=product.id,
                unit_amount=plan[f"{cycle}_price_cents"],
                currency=plan.get("currency", "usd"),
                recurring={"interval": interval},
                lookup_key=lookup_key,
            )
            prices[cycle] = price
            self.stdout.write(self.style.SUCCESS(f"Created price {price.id} ({lookup_key})."))
        return prices

    @staticmethod
    def _lookup_key(plan: dict, cycle: str) -> str:
        return f"{LOOKUP_KEY_PREFIX}_{plan['key']}_{cycle}"


if __name__ == "__main__":  # pragma: no cover
    sys.exit("Run via `python manage.py seed_example_billing`.")
