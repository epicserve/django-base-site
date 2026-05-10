<h1 align="center">Django Base Site</h1>
<p align="center">
  <a href="https://github.com/epicserve/django-base-site/actions/workflows/ci.yml">
    <img src="https://github.com/epicserve/django-base-site/actions/workflows/ci.yml/badge.svg?branch=main&event=push" alt="CI">
  </a>
  <a href="https://django-base-site.readthedocs.io/en/latest/?badge=latest">
    <img src="https://readthedocs.org/projects/django-base-site/badge/?version=latest" alt="Documentation Status">
  </a>
  <a href="https://github.com/epicserve/django-base-site/blob/main/LICENSE.md">
    <img src="https://img.shields.io/github/license/epicserve/django-base-site.svg" alt="license">
  </a>
</p>

**Documentation**: [django-base-site.readthedocs.org](http://django-base-site.readthedocs.org/)  
**Source Code**: [github.com/epicserve/django-base-site](https://github.com/epicserve/django-base-site/)

---

<!--intro-start-->
The Django Base Site is an opinionated starter template to jump-start any new Django project. It has been lovingly
maintained for over twelve years and has been used to jump-start many other projects. Because it is organized logically,
it will help you and your team collaborate and stay organized as your project grows. All the best practices and tools
are used to help you save days of mundane setup and tooling! This Django boilerplate/starter template will help you or
your team deploy your site to production in minutes instead of days.

To get started, jump to the [installation](#installation) section or keep reading to learn more about the included
features.
<!--intro-end-->

<!--readme-start-->

## ✨ Features

### 🧑‍💻 Best Practices

* [Epicenv](https://github.com/epicserve/epicenv) - A delightful environment variable manager with schema validation, type coercion, and CLI tools for generating `.env` files. See the [epicenv documentation](https://github.com/epicserve/epicenv#readme) for more details.
* [Docker](https://www.docker.com/) - Docker Compose for development with healthchecks on every service, plus a multi-stage Dockerfile for a production-ready image.
* [Mailpit](https://mailpit.axllent.org/) - Local SMTP capture with a web UI at http://localhost:8025
* [MinIO](https://min.io/) - S3-compatible object storage for local media uploads (avatars, etc.) with a console at http://localhost:9001
* [UV](https://github.com/astral-sh/uv) - Used to maintain Python requirements
* [Just](https://github.com/casey/just) - Popular tool for running common commands (make equivalent)
* [python-json-logger](https://github.com/madzak/python-json-logger) and [readable-log-formatter](https://github.com/ipmb/readable-log-formatter) - JSON logging for better log parsing

### 📦️ Django Packages

* [Django 5](https://www.djangoproject.com/) - Latest version of Django
* [Custom User Model][custom_user_model] - Extends `AbstractUser` with per-user `timezone` (auto-detected from the browser via middleware) and avatar fields (uploaded to MinIO/S3 with crop data).
* [Django Allauth](http://www.intenct.nl/projects/django-allauth/) (headless) - JSON auth API with full MFA support: TOTP, recovery codes, and WebAuthn passkeys (via [`fido2`](https://github.com/Yubico/python-fido2)).
* [Django Ninja](https://django-ninja.dev/) - Fast type-safe API framework powering `/api/app-context/`, the user/avatar endpoints, organizations, teams, and the public invite flow.
* [Django Hijack](https://github.com/django-hijack/django-hijack) - Staff impersonation with a SPA-driven user search, gated by a `staff_only` permission check.
* [Celery](http://docs.celeryproject.org/) - Most popular task runner for running asynchronous tasks in the background.
* [Gunicorn](https://gunicorn.org/) - Production WSGI server (4 workers × 2 threads), configured at `gunicorn.conf.py`.
* [WhiteNoise](https://whitenoise.readthedocs.io/) - Serves Vite-hashed assets in production with `Cache-Control: max-age=31536000, immutable`.
* [Django Storages](https://django-storages.readthedocs.io/) + boto3 - S3-compatible media storage with a custom backend (`apps.base.storage.S3MediaStorage`) that handles the Docker-internal vs. browser endpoint URL split for MinIO.
* [Django Alive](https://github.com/lincolnloop/django-alive/) - Health-check endpoints
* [Django Maintenance Mode](https://github.com/fabiocaccamo/django-maintenance-mode) - Drop the site into a maintenance window.
* [Django SES](https://github.com/django-ses/django-ses) - Production email backend.

[custom_user_model]: https://docs.djangoproject.com/en/stable/topics/auth/customizing/#substituting-a-custom-user-model

### 🧩 Custom Django Applications

These first-party apps under `apps/` are the foundation for any B2B SaaS built on this template.

* **`apps/organizations/`** — multi-tenant scaffolding: `Organization`, `OrganizationMember` (with `is_owner` / `is_primary` flags), and `OrganizationInvite` models. `OrganizationMiddleware` lazy-loads `request.org` from the session; an org switcher lives in the user-menu navbar. The accept-invite flow lives in the SPA at `/organizations/invite/:key/accept/` and works for anonymous visitors via a sign-in / sign-up roundtrip with `?next=`.
* **`apps/teams/`** — generic `Team` model (organization FK + M2M users) with full CRUD ninja API.
* **`apps/notifications/`** — `Notification` model (recipient + org + GenericForeignKey target) and `NotificationPreference` model, ninja API at `/api/notifications/` (list, unread-count, bulk, per-row patch/delete, per-user category preferences), a `notify()` producer service, retention via the `purge_expired_notifications` celery beat task and the `purge_notifications` management command, and a bell-dropdown UI with 20-second polling that pauses on hidden tabs. Producers register their models in `settings.NOTIFICATIONS_TARGET_MODELS` so target deletes cascade-clean their notifications, and declare categories in `settings.NOTIFICATIONS_CATEGORIES` so users can opt channels in or out per category.

### 🔧 Python Testing Tools

* [Pytest](https://docs.pytest.org/) - The most popular Python test runner in the Python community
* [Pytest Django](https://pytest-django.readthedocs.io/en/latest/index.html) - Django plugin for Pytest
* [Pytest-cov](https://pytest-cov.readthedocs.io) - Code coverage
* [Pytest Playwright](https://playwright.dev/python/docs/test-runners) - End-to-end tests live under `e2e/` and run against a dedicated `config.settings.e2e` settings module with pre-built Vite assets.
* [Model Bakery](https://github.com/model-bakers/model_bakery) - Faster fixture creation
* [Django Test Plus](https://github.com/revsys/django-test-plus/) - Helper functions to write tests faster
* [pyotp](https://github.com/pyauth/pyotp) - Used in the MFA / TOTP test suite

### 🐛 Debugging Support

* **Remote Debugging** - Full debugging support for PyCharm, VS Code, LazyVim/Neovim, and any DAP-compatible editor
* **One Command Setup** - Start debugging with `just start_with_debugpy`
* **PyCharm Integration** - Native Docker Compose debugging support with hot-reload
* **VS Code Integration** - Pre-configured launch configurations and tasks
* **[Detailed Documentation](docs/debugging.md)** - Complete setup guides for all supported editors

### 🩺 Code Quality, Formatting, and Linting Tools

* [Ruff](https://github.com/charliermarsh/ruff) - Python formatting and linting (replaces Black and friends, written in Rust).
* [Ty](https://github.com/astral-sh/ty) - Python type checking
* [dj Lint](https://djlint.com/) - Automatic Django HTML template formatting and linting
* [Django Debug Toolbar](https://github.com/jazzband/django-debug-toolbar) - Inspect query counts, settings, and templates in DEBUG.
* [Eslint](https://eslint.org/) (flat config) with [`eslint-plugin-vue`](https://eslint.vuejs.org/) - JS/Vue linting

### 💄 Frontend

* [Vue 3](https://vuejs.org/) SPA - Lazy-loaded routes via [Vue Router 5](https://router.vuejs.org/), reactive app store, theme-applied-before-CSS to prevent flash, version watcher with deploy-update banner.
* [Tailwind CSS v4](https://tailwindcss.com/) - Utility-first styling with the @tailwindcss/vite plugin and a custom `dark` variant driven by `data-theme`.
* [Vite 8](https://vitejs.dev/) - Frontend build tool. Hashed-asset cache + manifest support so WhiteNoise can serve them with immutable headers.
* [bun](https://bun.sh/) - Fast JS toolchain (replaces npm). The `frontend` Docker service is built from `oven/bun:1`.
* [@heroicons/vue](https://github.com/tailwindlabs/heroicons), [vue-advanced-cropper](https://norserium.github.io/vue-advanced-cropper/), [reka-ui](https://reka-ui.com/) - UI primitives.
* Account settings (General, Email, Password change, Security with TOTP / recovery codes / passkeys, Notifications), org settings (General, Members + Invites, Teams, Billing), notification bell with polling and a `/notifications/` archive page, public `/pricing/` page, Test Notifications and Impersonate views (superuser/staff).

### 💳 Billing (opt-in)

Stripe-backed subscriptions tied to Organizations. Off by default — set `BILLING_ENABLED=true` to turn on.

* `apps/billing/` with `BillingCustomer`, `Subscription`, and `WebhookEvent` models. Stripe is the source of truth; we mirror just enough locally to gate features and render the billing UI.
* Settings-declared plan + feature registries (`BILLING_PLANS`, `BILLING_FEATURES`) — same pattern as `NOTIFICATIONS_CATEGORIES`. Plans support monthly/annual prices, free tier, trial periods, per-seat pricing, and a "highlighted" flag for the popular plan.
* [Stripe Checkout](https://docs.stripe.com/payments/checkout) (full-page redirect) for new subscriptions and [Stripe Customer Portal](https://docs.stripe.com/customer-management) for upgrades, cancels, payment-method updates, and invoice history. Coupons / promotion codes are accepted at Checkout.
* Webhook at `/webhooks/stripe/` with HMAC signature verification and `WebhookEvent`-backed dedupe of Stripe retries.
* Per-seat sync — adding/removing org members updates Stripe quantity via `transaction.on_commit` in a `OrganizationMember` `post_save`/`post_delete` receiver.
* Trial-ending reminders + drift-recovery reconcile run as celery beat tasks.
* Feature gating: `appStore.hasFeature('teams')` in the SPA, `org_has_feature(org, 'teams')` and `@requires_feature('teams')` in Python. When `BILLING_ENABLED=False`, every feature falls through to its declared default so the starter template runs without Stripe credentials.
* Local dev: `stripe listen --forward-to http://localhost:8000/webhooks/stripe/` to bridge the test-mode webhooks.

### 📝 Documentation

The Django Base Site uses [MkDocs](https://www.mkdocs.org/) for documentation. You can copy the
[config file](https://github.com/epicserve/django-base-site/blob/main/config/mkdocs.yml) and the
[docs](https://github.com/epicserve/django-base-site/tree/main/docs) directory to help jumpstart the documentation for
your new project. The following are MkDocs plugins being used:

* [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) - Beautify MkDocs theme
* [mkdocstrings](https://mkdocstrings.github.io/) - Build documentation from Python docstrings
* [mkdocs-include-markdown-plugin](https://github.com/mondeja/mkdocs-include-markdown-plugin) - Include docs from other
  files
* [mkdocs-linkcheck](https://github.com/byrnereese/linkchecker-mkdocs) - Automatic link checking

## Installation

### Requirements

Before proceeding make sure you have installed [Docker](https://docs.docker.com/engine/installation/) and
[Just](https://github.com/casey/just#installation). Docker with Docker Compose is used for local development and Just is
used for common project commands.

### Quickstart Install Script

Copy and paste the following into your terminal to run the install script:

```bash
bash <(curl -s https://raw.githubusercontent.com/epicserve/django-base-site/main/scripts/start_new_project)
```

Running the script mostly does the same thing as manual method. The exception is that the install script has
questions to customize your new project setup.

**Note:** When starting the Django runserver it will take several seconds before the CSS styles take effect. This is
because Vite is running in dev mode which takes a few seconds to take effect.

Example output:

    $ cd ~/Sites
    $ bash <(curl -s https://raw.githubusercontent.com/epicserve/django-base-site/main/scripts/start_new_project)
    
    What is the project name slug [example]?
    What directory do you want your project in [/Users/brento/Sites/example]?

    Done.

    To start Docker Compose run:
    $ cd /Users/brento/Sites/example
    $ just start

### Manual Installation

    $ curl -LOk https://github.com/epicserve/django-base-site/archive/main.zip && unzip main
    $ mv django-base-site-main example
    $ cd example
    $ uvx epicenv create        # Generates .env from the schema in .env.toml
    $ just clean_extra_files
    $ find ./public -name ".keep" | xargs rm -rf
    $ just start

`epicenv create` reads the `[variables]` block in `.env.toml` and produces a `.env` with sensible defaults — `SECRET_KEY` and `POSTGRES_PASSWORD` are auto-generated, `SITE_DOMAIN=localhost:8000` (so passkeys work), and the MinIO + Mailpit credentials are pre-wired.

## Usage

### Dev URLs

Once `just start` is up, the following are available:

| URL                                | What                                                  |
|------------------------------------|-------------------------------------------------------|
| http://localhost:8000/             | Vue SPA (Django serves the shell, SPA owns routing)   |
| http://localhost:8000/admin/       | Django admin                                          |
| http://localhost:8000/api/docs     | Live OpenAPI spec for the ninja API (DEBUG only)      |
| http://localhost:3000/             | Vite dev server (HMR; usually proxied transparently)  |
| http://localhost:8025/             | Mailpit — inspect outgoing emails                     |
| http://localhost:9001/             | MinIO console — browse the media bucket               |

> **Note**: Use `http://localhost:8000/` rather than `http://127.0.0.1:8000/` so passkey enrollment works — WebAuthn rejects bare IP addresses as Relying Party IDs.

### Django superuser

On a fresh project run `just init` — it brings services up, runs `just create_superuser` (which calls the idempotent `epicenv create-superuser`), then attaches to the foreground logs like a normal `just start`. Use `just start` for every subsequent boot so you don't pay the setup overhead each time.

Two ways to provide credentials:

* **Env-var path (simplest).** Set `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, and `DJANGO_SUPERUSER_PASSWORD` in `.env` (the variables are declared in `.env.toml` with empty defaults). `just init` and `just create_superuser` both pick them up automatically through the container env. If `DJANGO_SUPERUSER_USERNAME` is blank, the recipe skips with a friendly message — so `just init` is safe to run before you've decided on a superuser strategy.
* **Secrets-manager path.** The `create_superuser` recipe lives in your project's top-level `justfile` so you can edit it in place. Replace the default body with a pipeline that fetches credentials from your secrets manager and pipes JSON into `epicenv create-superuser`. Example for 1Password:

  ```just
  create_superuser:
      #!/usr/bin/env bash
      docker compose up --wait -d web
      uvx epicenv secrets get op://Private/django-admin \
          --fields username,email,password \
          | docker compose exec -T web epicenv create-superuser
  ```

  Since `epicenv create-superuser` honors stdin first and env vars last, piped credentials take priority over anything in `.env`. `just create_superuser` brings the `web` container up if it isn't already, so it's runnable on demand any time (e.g., after rotating the admin password).

### Just commands

The Django Base Site comes with Just recipes for all the most common commands and tasks. To see the full list run `just` in the root of the project. Common ones:

```
init                         # First-time setup: services up + create_superuser + attach (use just start subsequently)
start                        # docker compose up
start_with_debugpy           # Start with debugpy listening on :5678
stop                         # Stop all services
build                        # Rebuild Docker images + collectstatic
build_frontend               # bun run build + collectstatic
clean                        # Remove build files, caches, coverage data
collectstatic                # Run Django's collectstatic
format                       # Format Python (ruff), JS (eslint), HTML (djlint), justfile
lint                         # Run all linters + ty type check + check for missing migrations
test                         # pytest (Django + ninja API tests)
test_with_coverage           # pytest --cov, then open the HTML report
test_e2e [args]              # Build the frontend, then run the Playwright e2e suite
db_dump                      # pg_dump to ~/Downloads
db_restore [dump_file]       # Restore from the latest dump (or a specific file)
upgrade_python_packages      # uv sync --all-packages --all-extras
upgrade_node_packages        # bun update
create_env                   # Generate .env from the schema in .env.toml
create_superuser             # Idempotent epicenv create-superuser (override to pipe from a secrets manager)
```

## Deploying to Production

The Django base site is designed to be production ready because it comes with a production
ready [multi-stage Dockerfile](https://github.com/epicserve/django-base-site/blob/main/config/docker/Dockerfile.web).
You can also read a [blog post](https://epicserve.com/django/2022/12/30/using-flyio-with-the-django-base-site.html)
about using it with fly.io. If you want to blog about using the Django Base Site with other PaaS providers, please let
me know, and I can link to the post here.

## Contribute

1. Look for an open [issue](https://github.com/epicserve/django-base-site/issues) or create new issue to get a dialog
   going about the new feature or bug that you've discovered.
2. Fork the [repository](https://github.com/epicserve/django-base-site) on GitHub to start making your changes to the
   main branch (or branch off of it).
4. Make a pull request.

<!--readme-end-->
