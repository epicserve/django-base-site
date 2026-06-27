# CHANGELOG


## 2026-06-27

### Added

* Git hooks that run the code quality checks automatically. A `pre-commit` hook runs `just format` and a `pre-push` hook runs `just lint`. Hooks live in the version-controlled `.githooks/` directory and are enabled with `git config core.hooksPath` (rather than copying into `.git/hooks/`), so they're reviewable and travel with the repo. New `just install_hooks` recipe installs them; `just init` now installs them automatically. Since `just format` reformats the whole working tree, the `pre-commit` hook re-stages the files you'd already staged so the fixes are committed — but it aborts if a file is only partially staged (`git add -p`), to avoid sneaking unstaged hunks into the commit. Bypass any hook with `--no-verify`.

### Changed

* ESLint -> [Oxlint](https://oxc.rs/docs/guide/usage/linter) + [Oxfmt](https://oxc.rs/docs/guide/usage/formatter) for JavaScript/Vue linting and formatting. Rust-based, ESLint / Prettier-compatible config formats. Removes `@eslint/js`, `eslint`, `eslint-plugin-vue`, and `globals` in favor of `oxlint` (1.71.0) and `oxfmt` (0.56.0, exact-pinned since Oxfmt is still in beta). Configs live at `.oxlintrc.json` and `.oxfmtrc.json`; `eslint.config.mjs` deleted. The `.oxlintrc.json` `plugins` list explicitly includes `eslint` (setting `plugins` overwrites the default set, so the `eslint`-core rules — `no-console`, `no-debugger`, `no-param-reassign` — must be re-listed to stay active). `.oxfmtrc.json` uses `singleQuote: true` uniformly, so CSS (both `app.css` and `.vue` `<style>` blocks) matches the codebase's single-quote convention.

### Removed

* `<template>` block linting from `eslint-plugin-vue` (Oxlint only lints the `<script>` block of `.vue` SFCs). Templates are still formatted by Oxfmt. The old `one-var`, `max-len`, and `no-underscore-dangle` ESLint rules have no enabled Oxlint equivalent — line length is now handled by Oxfmt's `printWidth: 120`, and the now-defunct `eslint-disable` comments for those rules were dropped.

### CI

* `lint_js` (and the CI `Lint` job, via `just lint`) now runs `oxfmt --check` in addition to `oxlint`, so formatting drift is caught in CI — mirroring the Python side's `ruff format --check`. ESLint previously combined linting and formatting in one pass; splitting into Oxlint + Oxfmt would otherwise have dropped format verification from CI.


## 2026-05-30

### Changed

* The sign-in page (`frontend/js/accounts/views/LoginView.vue`) now automatically attempts passkey/WebAuthn sign-in on mount when the browser supports it, opening the credential selector without requiring a click. The existing **Sign in with a passkey** button is preserved as an explicit fallback/manual trigger. A new `attemptPasskeyLogin(isAuto)` helper backs both paths: auto attempts stay silent on common gesture-related rejections (`NotAllowedError` / `AbortError`), while explicit button clicks retain the full loading/error UX. A `passkeyInFlight` guard prevents the auto and manual triggers from overlapping.
* Documentation system migrated from MkDocs + Material for MkDocs to **[Zensical](https://zensical.org/)** (the official successor by the same team).
  - Configuration moved to native `zensical.toml` at the project root (replaced `config/mkdocs.yml`).
  - Removed `mkdocs-include-markdown-plugin`. Content includes now use `pymdownx.snippets` (e.g. `docs/index.md` pulls sections from `README.md`; `docs/changelog.md` includes the full `CHANGELOG.md`).
  - Restored `docs/index.md` to include the main README content via snippets, plus a new "Working on the Documentation" section.
  - New Just commands: `just docs` (serve on port 4000), `just docs-build`, `just docs-lint` (added to `config/base.just` in alphabetical order).
  - Local documentation server now runs on port 4000 by default (`dev_addr` in `zensical.toml`) to avoid conflict with Django.
  - Removed the `docs` service and `full`/`docs` profiles from `compose.yml`.
  - Updated `.readthedocs.yaml` to use `zensical build`.
  - Navigation improvements: added `navigation.indexes`, set `title: Overview` on the index page via frontmatter, and expanded features in `zensical.toml` while remaining on the `classic` theme variant.
  - Cleaned up old MkDocs references across the project (README, CLAUDE.md, docs, etc.).


## 2026-05-23

### Added

* `apps/billing/example_plans.py` — bundled Free / Pro / Business three-tier demo, opt-in via the new `BILLING_USE_EXAMPLE_PLANS` env var (registered in `.env.toml`, default `false`). When the flag is on, `config/settings/_base.py` imports `BILLING_PLANS` and `BILLING_FEATURES` from the example module instead of leaving them empty. Lets the maintainer (and anyone evaluating the template) dogfood the billing UX without editing settings and dragging a 70-line diff through unrelated work. The conditional import only fires when the flag is set, so the default startup path never touches `apps.billing`. See the new "Dogfooding locally" section in [docs/billing.md](docs/billing.md).
* `python manage.py seed_example_billing` — idempotent Stripe seeder that creates Pro + Business products and prices in test mode, then prints the four `STRIPE_PRICE_*` env-var lines to paste into `.env`. Pairs with `BILLING_USE_EXAMPLE_PLANS=true` for a one-command dogfood setup. Idempotency comes from Stripe's `lookup_key` on prices and a `djbs_seed_key` metadata marker on products — rerunning the command never creates duplicates. Refuses to run against `sk_live_…` keys unless `--force-live` is passed. The `/pricing/` empty-state page now points staff users at this command with a three-step recipe instead of the one-liner "add entries to `BILLING_PLANS`".


## 2026-05-22

### Added

* Django superuser hook via `just init` + `epicenv create-superuser`. New `DJANGO_SUPERUSER_USERNAME` / `_EMAIL` / `_PASSWORD` variables in `.env.toml` declare the credentials (left blank by default); `just init` brings services up, runs the new idempotent `create_superuser` recipe in the top-level `justfile`, then hands off to `just start`. The recipe skips with a friendly message when `DJANGO_SUPERUSER_USERNAME` is blank, brings the `web` container up if it isn't already, and is safe to run standalone any time (e.g., after rotating the admin password). Teams using a secrets manager edit the `create_superuser` recipe in place to pipe credentials from 1Password (or similar) into `docker compose exec -T web epicenv create-superuser`. `scripts/start_new_project` now instructs developers to run `just init` the first time and `just start` for every subsequent boot.

### Changed

* Upgraded `epicenv[django]` to v1.6.2. Bumps the `uvx epicenv@…` pins in `scripts/start_new_project` and the `just create_env` recipe to `1.6.2`, and refreshes the `[tool.uv.exclude-newer-package]` settle date so `uv sync` (both locally and in `Dockerfile.web`) can resolve the new release. v1.6.2 also patches a non-blocking-stdin bug in `epicenv create-superuser` that made it miss JSON piped from any slow upstream (`uvx epicenv secrets get …`, `op item get`, etc.) — the secrets-manager example in the `create_superuser` recipe now works as a plain pipeline without needing a bash-shebang workaround.


## 2026-05-15

### Changed

* Upgraded `epicenv[django]` to v1.4 and moved the env schema from `[tool.epicenv.variables]` in `pyproject.toml` to a dedicated `.env.toml` file at the project root. Every variable uses the multi-line `[variables.NAME]` form for a uniform layout.
* Pinned the exact epicenv version used by `scripts/start_new_project` and the `just create_env` recipe (`uvx epicenv@1.4.0 create`) so new project bootstraps remain reproducible.


## 2026-05-09 (later)

### Added

* `apps/billing/` — opt-in Stripe subscriptions tied to Organizations. Models: `BillingCustomer` (one Stripe customer per org, survives cancellation), `Subscription` (local mirror of the active Stripe sub with status / billing_cycle / quantity / period and trial dates), `WebhookEvent` (idempotency dedupe for Stripe retries). Settings-declared plan + feature registries follow the `NOTIFICATIONS_CATEGORIES` pattern (`BILLING_PLANS` and `BILLING_FEATURES` in `_base.py`); plans are loaded into `apps/billing/plans.py` `Plan` dataclasses and features into `apps/billing/features.py` `Feature` dataclasses.
* Ninja API at `/api/billing/` (mounted only when `BILLING_ENABLED=true`): `GET /plans/` + `GET /features/` (public, drive the pricing page), `GET /subscription/` (owner-only current state), `POST /checkout/` (returns Stripe Checkout URL — full-page redirect), `POST /portal/` (returns Stripe Customer Portal URL — handles upgrade/downgrade/cancel/payment-methods/invoices). Checkout sets `allow_promotion_codes=True` so coupon codes work; `subscription_data.trial_period_days` is set on the first subscription only (Stripe rejects trials on subsequent subs for the same customer).
* Stripe webhook at `/webhooks/stripe/` (mounted only when `BILLING_ENABLED=true`, registered in `config/urls.py` before the SPA catch-all). Verifies signatures with `stripe.Webhook.construct_event`, dedupes via `WebhookEvent`, handles `checkout.session.completed`, `customer.subscription.{created,updated,deleted}`, `invoice.payment_{succeeded,failed}` — sends in-app notifications + emails on `payment_failed` and `subscription_deleted`.
* `org_has_feature(org, key)` / `org_feature_value(org, key)` helpers in `apps/billing/access.py` plus a `requires_feature` decorator that 402-Payment-Required's missing features. When `BILLING_ENABLED=False`, gates fall through to feature defaults so the starter template runs out of the box without Stripe credentials.
* Per-seat pricing — `OrganizationMember` `post_save`/`post_delete` receivers schedule `transaction.on_commit(sync_seat_quantity)` so the Stripe quantity update fires after the membership change commits. No-ops for non-seat-based plans, free plans, and disabled billing.
* Trial reminders — `check_trials_ending` celery beat task (daily 04:00 UTC) sends `billing_trial_ending` notifications + emails 3 days before `trial_end`, idempotent via `Subscription.trial_ending_notified_at`.
* Drift recovery — `reconcile_subscriptions` celery beat task (weekly Mon 05:00 UTC) iterates all `BillingCustomer` rows and re-syncs from Stripe, defending against missed webhooks.
* `app_context.billing` block in `/api/app-context/` — exposes `enabled`, `plan`, `status`, `trial_end`, `cancel_at_period_end`, and a resolved `features` map. SPA store (`frontend/js/stores/app.js`) surfaces `appStore.hasFeature(key)` / `appStore.featureValue(key, fallback)`.
* `/pricing/` SPA page (`PricingView.vue`) — public (uses `MarketingLayout.vue`), monthly/annual toggle, plan cards with smart CTA logic (Sign up / Create org / Subscribe / Switch / Current). Hidden when `BILLING_ENABLED=false` via a router guard.
* Org Settings → **Billing** tab (`BillingView.vue`, route `/organizations/:slug/settings/billing/`) — current plan + status badge, trial countdown, "open Stripe portal" button, seat info, change-plan link to `/pricing/`. Handles the post-checkout webhook race by polling `GET /api/billing/subscription/` until the sub becomes active. Tab is conditionally appended in `OrgSettingsLayout.vue` only when billing is enabled.
* `<FeatureGate feature="X">` Vue component + `useFeature(key)` composable for declarative gating; `useBilling()` composable owns the subscription/plans state and the subscribe / portal / poll-until-active actions.
* `TrialEndingBanner.vue` (dismissible, keyed on `trial_end`) and `PastDueBanner.vue` (non-dismissible, links to portal) mounted at the top of `AppLayout.vue`.
* `frontend/js/views/settings/TeamsView.vue` is now wrapped in `<FeatureGate feature="teams">` with an upgrade-prompt fallback so non-paying orgs see a CTA instead of the teams UI.
* Email templates under `apps/billing/templates/billing/emails/`: `payment_failed`, `subscription_canceled`, `trial_ending` (multipart text + HTML, matching the existing template pattern).
* `BILLING_ENABLED`, `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET` registered in the epicenv schema. `apps/billing/apps.py:ready()` hard-fails at startup with `ImproperlyConfigured` when billing is enabled but keys are missing or any non-free plan lacks a Stripe price ID.
* `stripe~=14.0` added to `pyproject.toml` dependencies.

### Changed

* `apps.base.utils.email.send_email` now accepts `sending_user=None` for system-generated emails (e.g. billing webhook handlers); when `None`, the `Reply-To` header is omitted.
* `apps/base/api.py` `app_context` includes a `billing` block with feature-flag map even when `BILLING_ENABLED=False` (all features fall through to their declared defaults).
* `App.vue` skips wrapping in `AppLayout` when the route declares `meta.publicChrome=true` so the public `/pricing/` page renders its own `MarketingLayout` chrome instead of the in-app nav.


## 2026-05-09

### Added

* `apps/notifications/` — `Notification` (recipient + org + GenericForeignKey target) and `NotificationPreference` models, ninja API at `/api/notifications/` (list, unread-count, bulk, per-row patch/delete, prefs), a `notify()` service helper, category-and-channel preferences (`settings.NOTIFICATIONS_CATEGORIES` + `NotificationChannel`), per-row + retention-window purge via the `purge_expired_notifications` celery beat task and the `purge_notifications` management command, and a `post_delete` cleanup signal driven by `settings.NOTIFICATIONS_TARGET_MODELS` so target deletes don't leave orphans. `notify()` validates that recipients are members of the supplied organization.
* `AppNotificationBell.vue` + `useNotifications.js` composable — bell dropdown with Unread/All tabs, select-mode + bulk actions, click-outside, 20-second polling that pauses on `visibilitychange`, toast on new arrivals, and an `AppModal`-driven detail view for notifications with no navigable URL. Keyboard accessible: list rows are focusable + Enter/Space trigger actions, Escape closes the dropdown, and the unread badge announces via `aria-live`.
* `/notifications/` SPA page — full paginated archive with the same Unread/All tabs, select-mode, and bulk actions as the bell. Linked from the bell footer.
* Account settings **Notifications** tab (`AccountNotificationsView.vue`) for per-category in-app/email channel toggles.
* Embedded celery beat in the worker (`celery -A config worker -B`) and a `CELERY_BEAT_SCHEDULE` entry that runs the daily purge at 03:00 UTC via `crontab` — the comment in `_base.py` notes that production should run beat as a dedicated process.
* `NOTIFICATIONS_RETENTION_DAYS` env variable (default 90) registered in the epicenv schema.

### Changed

* Renamed the superuser **Send Test Email** view (`/send-test-emails/`) to **Test Notifications** (`/test-notifications/`). The form gains a "Send in-app notification" checkbox so the page can exercise both delivery channels; the API endpoint moved from `/api/send-test-email/` to `/api/test-notifications/` and validates that the recipient is a member of the sender's current org before creating an in-app row.
* `apps.base.utils.email.send_email` now accepts an optional `category=` argument; when set with User-instance recipients, recipients with the email channel disabled for that category are filtered out via `apps.notifications.categories.filter_recipients`.
* `compose.yml` worker command: `celery -A config worker` → `celery -A config worker -B` so the embedded beat runs the purge schedule for local dev.
* `.gitignore` now excludes `celerybeat-schedule*` produced by the embedded beat.


## 2026-05-02

### Added

* Vue 3 SPA frontend (replaces the Bootstrap 5 + plain JS stack). Mounted as the catch-all front door; Django serves the SPA shell HTML for every non-API path.
* django-allauth headless mode + MFA (TOTP, recovery codes, WebAuthn passkeys via `fido2`).
* `apps/organizations/` and `apps/teams/` apps as generic multi-tenant SaaS scaffolding (Organization, OrganizationMember with `is_owner` / `is_primary`, OrganizationInvite + accept-invite flow, OrganizationMiddleware, server-rendered accept-invite page; SPA org settings tabs for General/Members/Teams; org switcher in the user menu).
* Per-user `timezone` field on `User` with browser-detection modal and middleware that activates `request.user.timezone` per request.
* Profile photo upload with cropping (`vue-advanced-cropper`, Pillow thumbnail generation, MinIO storage).
* `django-hijack` for staff impersonation (staff-only permission check, SPA impersonate-search view).
* `django-ninja` API at `/api/` (app-context, version, send-test-email, users + avatar, organizations, teams).
* MinIO service for local media storage; `apps/base/storage.py:S3MediaStorage` handles the Docker-internal vs browser endpoint URL split.
* Playwright e2e tests for the auth flow (`pytest-playwright`, `config/settings/e2e.py`).
* Tailwind CSS v4 (replaces Bootstrap 5 + Sass) with theme-applied-before-CSS in the SPA shell.
* Toast notifications, theme toggle (light/dark/auto), version watcher with deploy-update banner, send-test-emails view (superuser only).
* WhiteNoise serving with immutable cache headers for hashed Vite assets in production.
* Self-hosted TOTP enrollment QR code (login-required `qr_svg` view backed by the `qrcode` package), replacing the previous third-party QR image service.
* `django-widget-tweaks` for the accept-invite template.

### Changed

* `npm` -> `bun` for the JS toolchain (`oven/bun:1` Docker image, `bun.lock`).
* `uwsgi` -> `gunicorn` (4 workers x 2 threads, `gunicorn.conf.py` at the repo root).
* `src/` -> `frontend/` (matches the eventual frontend/backend split).
* PostgreSQL 17 + Redis 7 + Mailpit + MinIO with healthchecks on every compose service.
* `SITE_DOMAIN` / `ALLOWED_HOSTS` now default to `localhost` (not `127.0.0.1`) — WebAuthn rejects bare IPs as Relying Party IDs.
* `vite_asset` template tag: dev-mode URLs no longer prepend `VITE_OUTPUT_DIR` (Vite serves from source paths in dev); `vite_asset` returns `""` for `.css` requests in dev (CSS is injected via JS HMR); production no longer emits a redundant `<link>` tag alongside the JS module (the script-module import pulls CSS automatically).
* `[tool.ty.rules]` configured to ignore the django-stubs noise rules (`unresolved-attribute`, `call-non-callable`, etc.) since ty's Django integration cannot model dynamic patterns like reverse managers, custom queryset methods, the swappable user model, or ninja's `Query`/`Path`/`Body` sentinels.
* `public/media/*` added to `.gitignore` (runtime uploads), keeping `public/media/.keep`.
* djLint ignore list extended to `H005,H021,H023` so email templates can keep their inline styles, `<html>` without `lang`, and entity references.

### Removed

* Bootstrap 5 + `crispy-forms` + `crispy-bootstrap5` (replaced by Tailwind + Vue components).
* Custom `SignInView`, `NameChange`, `SignInForm`, `NameForm`, and the legacy template-based allauth UI (replaced by the SPA + headless allauth + the user PATCH ninja endpoint).


## 2026-03-05

### Added

* Added [Mailpit](https://mailpit.axllent.org/) for local email capture with a web UI at http://localhost:8025
* Changed `ACCOUNT_EMAIL_VERIFICATION` from `"none"` to `"optional"` now that local email delivery works via Mailpit


## 2026-01-25

### Changed

* Upgraded epicenv to v1.2 and switched to using the built-in `epicenv.initializers.url_safe_password` function for generating `SECRET_KEY` and `POSTGRES_PASSWORD`


## 2026-01-24

### Added

* Added support for remote debugging with VS Code, PyCharm, and LazyVim/Neovim
* Added debugpy as a development dependency for Python debugging
* Added `just create_env` command for .env file generation with backup support
* Added comprehensive debugging documentation in docs/debugging.md
* Added debugging support section to README

### Changed

* Modernized navbar with offcanvas menu and improved mobile UX
* Improved VS Code debugging workflow with simplified two-step process
* Refactored ENABLE_DEBUGGER to USE_DEBUGPY for consistency
* Refactored .env creation into separate script with backup support
* Bumped uv-dependencies group with 7 updates
* Bumped development-dependencies group with 2 updates
* Bumped Node from 25.3 to 25.4

### Fixed

* Fixed jumbotron button overflow on mobile devices
* Fixed start_new_project script to work on Linux and enhanced CI verification


## 2025-12-19

### Changed

* Switched from MyPy to Ty for Python type checking. Ty is a fast, modern type checker from Astral that provides significantly better performance than MyPy.


## 2025-06-06

### Added

* Added CLAUDE.md with project overview and development commands for Claude Code
* Added Docker Compose healthchecks for PostgreSQL, Redis, and Vite services to ensure reliable service startup
* Added Docker build cache mounts for pip, uv, and npm with project-specific IDs to speed up builds
* Added .claude/ to .gitignore for local Claude Code settings
* Added Docker build cache mounts for apt update and install operations

### Changed

* Updated Docker Compose depends_on to wait for services to be healthy before starting dependent services
* Updated the `scripts/start_new_project` script with environment variables for docker compose build


## 2025-05-13

### Changed

* Changed Pytest to run tests using Postgres instead of SQLite.


## 2025-05-03

### Changed

* Switch to using `uv sync` and the `uv.lock` with `pyproject.toml` instead of `uv pip` with `*.in` requirement files.


## 2025-04-13

### Changed

* Make the default gravatar cartoon-style silhouetted outline of a person


## 2025-04-12

### Changed

* Improved the sign in UI/UX


## 2025-04-05

### Changed

* Switch to using `docker compose exec` instead of `docker compose run` for faster Just commands
* Switch to using the base_entrance.html template for Allauth, so templates that aren't overridden like the signup_closed.html template still work
* Update the Githut Action that creates a PR for Python upgrades so that it bolds upgrades greater than a patch

### Fixed

* Fix a JS exception in color picker
* Remove the extra double quote in the Github Action that creats a PR for Python upgrades
* Fix the browser trying to load the Favicon
* Fix the case for "AS" in the docker config file
* Fix linting errors


## 2024-10-04

### Fixed

* The quickstart script not replacing the project name in the compose.yml file.


## 2024-10-02

### Changed

* Updated ESLint to format config files
* Suppress SASS warnings until Bootstrap v5.3.4 is released


## 2024-10-02

### Changed

* Use [python-json-logger](https://github.com/madzak/python-json-logger) and [readable-log-formatter](https://github.com/ipmb/readable-log-formatter) for for better log parsing with JSON


## 2024-03-16

### Added

* Added Just commands to dump and restore the database


## 2024-03-11

### Changed

* Renamed the Just command build_assets to build_frontend
* Moved all common/base Just commands to the config/base.just file


## 2024-02-26

### Changed

* Switched to Ruff for linting and formatting Python. This replaces Bandit, Black, and isort.


## 2024-02-24

### Changed

* Switched to using UV instead of pip/pip-tools for managing Python requirements


## 2024-01-06

### Changed

* Upgraded to Python 3.12


## 2023-12-31

### Added

* Added the Just command update_everything to upgrade Python and Node

### Changed

* Upgraded to Django 5.0


## 2023-12-26

### Changed

* Refactor and clean up the vite_asset template tag
* Add tests for the vite_asset and vite_hmr_client template tags


## 2023-12-24

### Changed

* Upgrade from Vite 4.5 to 5.0 


## 2023-10-07

### Added

* Add the Django Maintenance Mode package


## 2023-09-23

### Added

* Add a gravatar property to the user model

### Changed

* Make the layout and style better for SaaS projects


## 2023-09-16

### Changed

* Updated Redis configuration settings to allow for a REDIS_PREFIX

### Added

* Added Django-alive for health checks
* Added a uwsgi.ini config file


## 2023-09-10

### Changed

* Upgrade the Python container from Debian buster to bookworm and pin the Python version to 3.11.*.


## 2023-08-31

### Changed

* Upgrade to version 3 of the Compose file
* Switch to using a named volume for node_modules.
* Switch to always upgrade npm on build


## 2023-08-29

### Changed

* Changed to using a root user for local development. This fixes an issue that was happening where Vite and other JS
  related tools where throwing write permission errors when running because the web service would create files as a
  non-privileged app user and then JS tools would run as a non-privileged user and then try to write to
  directories owned by root.


## 2023-06-01

### Changed

* Remove the Docker Compose volume for node for more consistent builds. This fixes the problem where sometimes you had
  to run `docker compose run node npm install` after running `docker compose build` to install the node modules into the
  local node volume. Instead the node modules are always installed into the docker image.

### Fixed

* Fixed Vite not being available after changes to package.json. This fixes [#289](https://github.com/epicserve/django-base-site/issues/289)


## 2023-04-01

### Added

* Add a pre_commit command to the justfile to run the lint, format, and test commands


## 2022-01-14

### Changed

* Removed the "Successfully signed in as" message after a user has signed in by add the ACCOUNT_SHOW_POST_LOGIN_MESSAGE
  setting with it set to False by default.
* By default, set ACCOUNT_EMAIL_VERIFICATION to "none" so that new hobby apps don't require transactional email set up.
* Changed ACCOUNT_USERNAME_REQUIRED to False and ACCOUNT_AUTHENTICATION_METHOD to "email" so you can signup and signin
  with just your email address.
* Changed ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE to False for a nicer sign-up experience

### Added

* Added the adapter apps.accounts.auth_adapter.AccountAdapter to add the new custom settings
* The ACCOUNT_SIGNUP_OPEN setting set it to false so signup is closed by default
* Bash aliases and Django bash completion


## 2022-12-31

### Added

* A color picker to toggle between dark and light mode

### Changed

* Upgraded to Bootstrap 5.3.0-alpha1 in order to add the color picker 


## 2022-12-27

### Added

* The packages django-test-plus and model-bakers
* More tests
* The upgrade_packages Just recipe
* Just recipes for removing docker containers, images, volumes
* Bandit for automatic security scanning


## 2022-12-26

### Added

* Just recipe, build_assets

### Changed

* Switch from the using docker-compose to using docker compose
* Updated Django settings, so you can use config/settings/test_runner.py for pytest
* Add the lock suffix to generated Python requirement files
* Clean up and add more arguments to the start project script


## 2022-12-18

### Added

* Instructions on how to deploy to Fly.io

### Changed

* Make changes to settings to make it easier to deploy to platforms like Fly.io


## 2022-12-17

### Changed

* Switched the session backend from django-redis-sessions to the native django.contrib.sessions.backends.cache backend.
* Switched from using django-redis-cache for parsing a REDIS_URL to using the native django.core.cache.backends.redis.RedisCache backend.
* Move the vite asset tags to the bottom script block.


## 2022-12-12

### Added

* Missing accounts migration

### Changed

* Update the Dockerfile so it could be used for production builds


## 2022-12-11

### Changed

* Upgrade to Vite 4.0


## 2022-12-10

### Changed

* Upgrade to Django 4.1
* Change python version to 3.11
* Move the Javascript config files for eslint, stylelint, and Vite from the root directory to src/config
* Change the mkdocs port from 5000 to 4000 since Airtunes/Airplay are taking that port
* Move the mkdocs.yml config to the docs directory
* Move the Docker files and requirement files under the config directory
* Switch from using Flake8 to using Ruff


## 2022-12-08

### Changed

* Switch from using Make for common commands to Just
