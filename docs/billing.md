# Billing (Stripe Subscriptions)

The starter ships with an opt-in Stripe billing app under `apps/billing/`. Subscriptions are tied to **Organizations**, not individual users — every org gets its own Stripe customer, its own subscription, and its own seat count.

Off by default. Set `BILLING_ENABLED=true` in your `.env` to turn it on. While off, the billing API and the Stripe webhook URL are unmounted, the SPA hides the pricing page and billing tab, and `apps.billing.access.org_has_feature()` returns each feature's declared default — so the template runs end-to-end without any Stripe credentials.

## Overview

* **Plans + features** are declared as plain dicts in `settings.BILLING_PLANS` and `settings.BILLING_FEATURES` ([config/settings/_base.py](../config/settings/_base.py)). Same pattern as `NOTIFICATIONS_CATEGORIES`. Plans support monthly + annual prices, a free tier, trial periods, per-seat pricing, and an `is_highlighted` flag for the "Popular" badge on the pricing page. A bundled three-tier example lives in [apps/billing/example_plans.py](../apps/billing/example_plans.py) and loads when `BILLING_USE_EXAMPLE_PLANS=true` — see "Dogfooding locally" below.
* **New subscriptions** go through [Stripe Checkout](https://docs.stripe.com/payments/checkout) (full-page redirect).
* **Existing subscriptions** are managed through the [Stripe Customer Portal](https://docs.stripe.com/customer-management) — payment methods, cancels, invoice history.
* **Webhook** at `/webhooks/stripe/` with HMAC signature verification. `WebhookEvent` rows dedupe Stripe retries.
* **Per-seat sync** — adding or removing an org member updates the Stripe subscription's quantity via a `transaction.on_commit` hook on `OrganizationMember`.
* **Trial reminders + drift recovery** run as Celery beat tasks (`apps/billing/tasks.py`).
* **Feature gating** — `appStore.hasFeature('teams')` in the SPA; `org_has_feature(org, 'teams')` and `@requires_feature('teams')` in Python.

## Local setup

### 1. Get Stripe test keys

From https://dashboard.stripe.com/test/apikeys, grab:

* `STRIPE_SECRET_KEY` — `sk_test_…`
* `STRIPE_PUBLISHABLE_KEY` — `pk_test_…`

### 2. Create products + prices

In test mode, create one product per non-free plan (Pro, Business). For each product create two prices — a monthly recurring price and an annual recurring price. Copy the `price_…` IDs into `.env`:

```
STRIPE_PRICE_PRO_MONTHLY=price_…
STRIPE_PRICE_PRO_ANNUAL=price_…
STRIPE_PRICE_BUSINESS_MONTHLY=price_…
STRIPE_PRICE_BUSINESS_ANNUAL=price_…
```

If you've renamed plans or added more, mirror them in [config/settings/_base.py](../config/settings/_base.py) `BILLING_PLANS` — each non-free plan needs `monthly_price_id` and `annual_price_id` fields wired to env vars. Or if you're just kicking the tires, skip this step and use the bundled example — see [Dogfooding locally](#dogfooding-locally) below.

### 3. Enable billing

```
BILLING_ENABLED=true
STRIPE_SECRET_KEY=sk_test_…
STRIPE_PUBLISHABLE_KEY=pk_test_…
```

Restart with `just stop && just start` so settings reload.

### 4. Forward webhooks with the Stripe CLI

Install the [Stripe CLI](https://docs.stripe.com/stripe-cli) (`brew install stripe/stripe-cli/stripe` on macOS / Linuxbrew), then:

```
stripe login
stripe listen --forward-to http://localhost:8000/webhooks/stripe/
```

The first time you run `stripe listen`, it prints a webhook signing secret (`whsec_…`). Copy it into `.env`:

```
STRIPE_WEBHOOK_SECRET=whsec_…
```

Restart again. Without `stripe listen` running, Stripe Checkout will succeed but your local app never hears about it — the local `Subscription` row only appears once the `checkout.session.completed` webhook fires.

### 5. Test cards

| Card | What it does |
|------|--------------|
| `4242 4242 4242 4242` | Succeeds, no 3DS |
| `4000 0025 0000 3155` | Requires 3DS authentication |
| `4000 0000 0000 9995` | Declines (insufficient funds) |

Any future expiry, any CVC, any ZIP. Full list at https://docs.stripe.com/testing.

## Testing locally

If you just want to see the billing UX end-to-end with realistic plans — without editing `config/settings/_base.py` or clicking around the Stripe Dashboard — there's a one-command path that uses the bundled Free / Pro / Business demo at [apps/billing/example_plans.py](../apps/billing/example_plans.py).

### 1. Set your Stripe test key

```
STRIPE_SECRET_KEY=sk_test_…
```

### 2. Seed Stripe

```
docker compose exec web python manage.py seed_example_billing
```

The command creates the Pro and Business products and their monthly + annual prices in your Stripe test account, then prints the four env-var lines you need. It's idempotent — rerunning it never creates duplicates (products are looked up by a `djbs_seed_key` metadata marker; prices use Stripe's first-class `lookup_key`). The command refuses to run against `sk_live_…` keys unless you pass `--force-live`.

### 3. Paste the printed lines into `.env` and flip the flag

```
BILLING_ENABLED=true
BILLING_USE_EXAMPLE_PLANS=true
STRIPE_PUBLISHABLE_KEY=pk_test_…
STRIPE_WEBHOOK_SECRET=whsec_…
STRIPE_PRICE_PRO_MONTHLY=price_…
STRIPE_PRICE_PRO_ANNUAL=price_…
STRIPE_PRICE_BUSINESS_MONTHLY=price_…
STRIPE_PRICE_BUSINESS_ANNUAL=price_…
```

`BILLING_USE_EXAMPLE_PLANS=true` loads the example plans into `settings.BILLING_PLANS` and `settings.BILLING_FEATURES` at startup. The flag has no effect when `BILLING_ENABLED=false`. When you're ready to ship your own plans, copy the structure from `example_plans.py` into `BILLING_PLANS` in `_base.py` and turn the flag off.

Restart with `just stop && just start`, then forward webhooks with `stripe listen` as in step 4 of [Local setup](#local-setup).

## Plan switching is disabled by default

When an org is already subscribed and visits `/pricing/`, the other plan cards show **"Already subscribed"** as a disabled state instead of inviting them to switch. The "Open billing portal" button on the billing settings page still works — it just doesn't expose a plan-switch flow.

Self-service plan switching is gated behind two things the starter can't decide for you:

1. **Stripe Dashboard configuration.** The Customer Portal only renders an "Update plan" section when you've turned on "Customers can switch plans" in https://dashboard.stripe.com/test/settings/billing/portal → Features → Subscriptions, and explicitly listed the products that should be switchable.
2. **Product decisions** — proration policy (immediate vs. next cycle vs. none), how to handle features the new plan no longer includes (e.g. existing `Team` rows when downgrading to a plan with `teams: false` — delete, archive, or banner?), and whether you want a save-the-account flow before letting a customer downgrade.

### Enabling plan switching

#### 1. Stripe Dashboard

* Go to https://dashboard.stripe.com/test/settings/billing/portal (and the live equivalent for production)
* **Features → Subscriptions →** toggle on **"Customers can switch plans"**
* Add the products you want exposed for switching (typically all your non-free plans, each with monthly + annual prices)
* Pick a proration behavior — "Prorate immediately" is the typical default
* Save

#### 2. Restore the SPA CTA

In [frontend/js/components/billing/PlanCard.vue](../frontend/js/components/billing/PlanCard.vue), the `if (props.hasSubscription)` branch in `ctaState` is currently a disabled "Already subscribed" state. Replace it with the original switch-plan CTA:

```js
if (props.hasSubscription) {
  return {
    label: props.plan.is_free ? 'Downgrade to Free' : 'Switch to this plan',
    action: () => billing.manageBilling(),
    disabled: false,
    hint: '',
  };
}
```

#### 3. Restore the "Change plan" section on the billing settings page

In [frontend/js/views/settings/BillingView.vue](../frontend/js/views/settings/BillingView.vue), add this section back near the bottom of the subscribed-state block (right after the seats section, inside the `<template>` for the subscribed state):

```html
<section class="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
  <h2 class="text-lg font-semibold text-gray-900 dark:text-white">
    Change plan
  </h2>
  <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
    Compare available plans and switch from the pricing page.
  </p>
  <RouterLink
    :to="{ name: 'pricing' }"
    class="mt-3 inline-block text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
  >
    View all plans →
  </RouterLink>
</section>
```

Optionally also update the "Manage billing" description to mention "change plans" again.

#### 4. Handle feature loss on downgrade

If a Business org with active teams downgrades to a Free plan that has `teams: false`, the existing `Team` rows stick around. `org_has_feature()` will return `False` for `teams`, so `@requires_feature('teams')` blocks new team creation — but the existing teams remain visible in the SPA until you decide what to do with them. Common patterns:

* **Hide** — gate the teams tab on `appStore.hasFeature('teams')`. Simplest, but data is invisible to the user.
* **Read-only with upgrade banner** — show the teams list but disable mutation actions; add a "Upgrade to manage teams" banner. Best UX, most work.
* **Archive on downgrade** — listen for `customer.subscription.updated` in the webhook, compare the old and new plan, soft-archive `Team` rows when a feature is lost. Cleanest data model, but irreversible without manual restore.

There's no universal right answer; pick what matches your product.

## Customizing plans and features

Plans and features are declared in [config/settings/_base.py](../config/settings/_base.py). The dicts are normalized into dataclasses in [apps/billing/plans.py](../apps/billing/plans.py) and [apps/billing/features.py](../apps/billing/features.py); the SPA fetches them from `/api/billing/plans/` and `/api/billing/features/`.

Each plan can declare:

| Field | Notes |
|-------|-------|
| `key` | Stable identifier — referenced by `plan_key` on `Subscription` rows. Don't rename in production. |
| `name`, `description` | Marketing copy shown on the pricing page. |
| `is_free` | Free tier — no checkout, no Stripe price IDs required. |
| `is_default` | The plan returned when an org has no subscription. |
| `is_highlighted` | Shows the "Popular" badge on the pricing card. |
| `monthly_price_id` / `annual_price_id` | Stripe `price_…` IDs. Required for non-free plans. |
| `monthly_price_cents` / `annual_price_cents` | Display-only price for the pricing page. Source of truth is Stripe. |
| `currency` | `usd`, `eur`, etc. |
| `trial_days` | Stripe-managed trial. Only applies on first subscription per org. |
| `seat_based` | If true, Stripe quantity = `OrganizationMember.objects.filter(organization=org).count()`. |
| `features` | Per-plan overrides for `BILLING_FEATURES` defaults. |

Features support two `type`s:

* `"bool"` — gate things on/off (`org_has_feature(org, 'teams')`).
* `"limit"` — numeric caps (`org_feature_limit(org, 'max_team_count')`).

Use them from Python with `@requires_feature('teams')` ([apps/billing/access.py](../apps/billing/access.py)) on view/api functions, or from Vue with `appStore.hasFeature('teams')` and `appStore.featureLimit('max_team_count')`.

## Production

1. Switch to **live mode** keys and **live mode** price IDs in your production env (`sk_live_…`, `pk_live_…`, live `price_…`).
2. Register the webhook in the Stripe Dashboard at https://dashboard.stripe.com/webhooks pointing at `https://your-domain/webhooks/stripe/`. Subscribe to at least: `checkout.session.completed`, `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_succeeded`, `invoice.payment_failed`.
3. Copy the live webhook's signing secret into `STRIPE_WEBHOOK_SECRET`.
4. If you enabled plan switching, configure the live Customer Portal at https://dashboard.stripe.com/settings/billing/portal — the test-mode config doesn't carry over.

## Where the code lives

| File | Purpose |
|------|---------|
| [apps/billing/models.py](../apps/billing/models.py) | `BillingCustomer`, `Subscription`, `WebhookEvent`. |
| [apps/billing/services.py](../apps/billing/services.py) | `get_or_create_customer`, `create_checkout_session`, `create_portal_session`, `sync_subscription_from_stripe`, `sync_seat_quantity`. Pure functions — callable from views, tasks, the shell. |
| [apps/billing/webhooks.py](../apps/billing/webhooks.py) | Stripe webhook handler with HMAC verification and event dedupe. |
| [apps/billing/access.py](../apps/billing/access.py) | `org_has_feature`, `org_feature_limit`, `@requires_feature`. |
| [apps/billing/api.py](../apps/billing/api.py) | Ninja router — `/api/billing/plans/`, `/api/billing/features/`, `/api/billing/subscription/`, `/api/billing/checkout/`, `/api/billing/portal/`. |
| [apps/billing/tasks.py](../apps/billing/tasks.py) | Celery beat tasks for trial reminders and drift reconcile. |
| [frontend/js/composables/useBilling.js](../frontend/js/composables/useBilling.js) | SPA composable — `subscribe()`, `manageBilling()`, `fetchSubscription()`, etc. |
| [frontend/js/views/PricingView.vue](../frontend/js/views/PricingView.vue) | Public pricing page. |
| [frontend/js/views/settings/BillingView.vue](../frontend/js/views/settings/BillingView.vue) | Org-scoped billing settings tab. |
