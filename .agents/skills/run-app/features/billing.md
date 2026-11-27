# Billing

Opt-in Stripe subscriptions for an organization: a public pricing page, Stripe Checkout to subscribe, and the Billing settings tab, which opens Stripe's Customer Portal for everything else. Plans and features are declared in settings (`BILLING_PLANS`, `BILLING_FEATURES`) and gate features such as teams.

## Off by Default

With `BILLING_ENABLED` off, as in a new project:

- `/api/billing/` and the Stripe webhook aren't mounted.
- The Billing tab is hidden, and `/pricing/` sends signed-in users home and others to the login page.
- Every feature check passes, so teams work.

To turn it on locally:

- Set `BILLING_ENABLED`, Stripe test keys (`STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`) and plan price IDs in `.env`, then restart `web` and `worker`. Without them, startup fails with `ImproperlyConfigured`.
- `BILLING_USE_EXAMPLE_PLANS` loads the Free, Pro and Business plans from `apps/billing/example_plans.py`.

## Routes

| Route | Name | Meta |
|---|---|---|
| `/pricing/` | `pricing` | `public`, `publicChrome` (its own header, works signed out) |
| `/organizations/<slug>/settings/billing/` | `org-settings-billing` | `requiresAuth`, `manage_billing` |

## Login

`owner@example.com` (Dunder Mifflin) for subscribing and the Billing tab. `member@example.com` sees the non-owner states.

## Pricing Page

`frontend/js/views/PricingView.vue`:

- **Header:** "Simple, Transparent Pricing", with the toggle "Monthly" / "Annual" (`aria-pressed`).
- **Back link:** "Back to Billing", "Back to Dashboard" or "Back to Sign In".
- **No plans:** "No plans configured yet.". Staff see setup steps; everyone else sees "Pricing coming soon.".
- **Plan buttons, by who's looking:**

| Who | Button |
|---|---|
| Signed out | "Get Started" (free plan) or "Sign Up" |
| No organization | "Create an Organization" |
| Not an owner | "Owner-Only" (disabled) |
| On this plan | "Current Plan" |
| Subscribed to another plan | "Already Subscribed" |
| Owner, free plan | "Use Free Plan" (disabled) |
| Owner, paid plan | "Subscribe" (goes to Stripe Checkout) |

## Billing Tab

`frontend/js/views/settings/BillingView.vue`:

- **No subscription:** "No Active Subscription" with "View Plans".
- **Subscribed:**
  - "Current Plan" with a status badge (Trial, Active, Past Due, Canceled, …).
  - When it renews or ends.
  - "Open Billing Portal" under "Manage Billing".
  - The "Seats" section, linking "Manage Members →".
- **Past due:** "Your last payment failed." with "Update Payment Method".
- **Back from Checkout** (`?checkout=success`): the toasts "Welcome! Activating your plan…", then "Your subscription is active.".
- **Without `manage_billing`:** "Only org owners can manage billing. Contact your owner to make changes.".
- **Banners in the header:** "Payment failed." ("Update Billing →"), and "Your trial ends in N days." ("Add a Payment Method", "Dismiss").

## What Stays Manual

- Stripe Checkout and the Customer Portal are full-page redirects to stripe.com. Stop at the redirect and report its URL.
- A subscription becomes active only through a signed webhook (`stripe listen --forward-to localhost:<web port>/webhooks/stripe/`). To see the subscribed states without Stripe, make a `Subscription` row with the recipes in `apps/billing/recipes.py` from `manage.py shell`.

## Endpoints

- `GET /api/billing/plans/` and `/api/billing/features/` (public)
- `GET /api/billing/subscription/`, `POST /api/billing/checkout/`, `POST /api/billing/portal/` (`manage_billing`)
- `/webhooks/stripe/`

## Known Issues

- `frontend/js/layouts/MarketingLayout.vue` isn't used: the pricing page draws its own header.

## Coverage

- No e2e tests: billing is off in the e2e settings.
- pytest: `apps/billing/tests/`, `apps/base/tests/test_app_context_api.py`
- Vitest: `frontend/js/utils/routeGuard.test.ts`, `frontend/js/utils/orgSettings.test.ts`
