# Billing

Opt-in Stripe subscriptions for an organization: a public pricing page, Stripe Checkout to subscribe, and the Billing settings tab, which opens Stripe's Customer Portal for everything else. Plans and features are declared in settings (`BILLING_PLANS`, `BILLING_FEATURES`) and gate features such as teams.

## Routes

| Route | Name | |
|---|---|---|
| `/pricing/` | `pricing` | Public, with its own header |
| `/organizations/<slug>/settings/billing/` | `org-settings-billing` | `requiresAuth`, `manage_billing` |

## Login and Data

**Billing is off by default.** With `BILLING_ENABLED` off, as in a new project, the Billing tab is hidden, `/pricing/` sends signed-in users home and others to the login page, and every feature check passes, so teams work. To turn it on:

1. Set `BILLING_ENABLED`, Stripe test keys (`STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`) and the plans' price IDs in `.env`. `BILLING_USE_EXAMPLE_PLANS` loads the Free, Pro and Business plans from `apps/billing/example_plans.py`.
2. Restart `web` and `worker`. Without the keys, startup fails with `ImproperlyConfigured`.

Then sign in as `owner@example.com` (Dunder Mifflin) to subscribe and use the Billing tab, or `member@example.com` for what a non-owner sees.

## Subscribing

1. As the owner, open the Billing tab. With no subscription it shows "No Active Subscription" with "View Plans".
2. Click "View Plans". On "Simple, Transparent Pricing", each paid plan has "Subscribe".
3. Click "Subscribe". The browser goes to Stripe Checkout on stripe.com. Stop there and report its URL.

The pricing page's plan buttons depend on who's looking: "Owner-Only" (disabled) for a member, "Create an Organization" with none selected, "Current Plan" and "Already Subscribed" once subscribed, and "Get Started" or "Sign Up" signed out.

## What Stays Manual

- **Stripe Checkout and the Customer Portal** are full-page redirects to stripe.com.
- **A subscription becomes active only through a signed webhook** (`stripe listen --forward-to localhost:<web port>/webhooks/stripe/`). To see the subscribed states without Stripe, make a `Subscription` row with the recipes in `apps/billing/recipes.py` from `manage.py shell`.

## Cleanup

- Delete any `Subscription` row you made; seeding doesn't touch billing.
- Put `BILLING_ENABLED` and the Stripe settings back as they were, and restart `web` and `worker`.

## Source and Tests

- `frontend/js/views/PricingView.vue`, `frontend/js/views/settings/BillingView.vue`. The API and webhook: `apps/billing/`.
- No e2e tests: billing is off in the e2e settings.
- pytest: `apps/billing/tests/`, `apps/base/tests/test_app_context_api.py`
- Vitest: `frontend/js/utils/routeGuard.test.ts`, `frontend/js/utils/orgSettings.test.ts`
