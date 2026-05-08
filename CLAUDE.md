# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django Base Site is an opinionated Django starter template with a production-ready foundation. The stack is Django 5 + django-ninja + django-allauth (headless mode, with MFA + WebAuthn passkeys) on the backend, and a Vue 3 SPA with Tailwind v4 on the frontend. Multi-tenant scaffolding (organizations, teams, invites) is built in. Celery + Redis for background tasks, MinIO for S3-compatible local media storage, gunicorn in production.

## Architecture

- **Apps**: Under `apps/` — `accounts/` (custom user with timezone + avatar fields), `base/` (utilities, ninja error handlers, storage backends, the SPA shell view, the `qr_svg` view, etc.), `organizations/` (Organization, OrganizationMember, OrganizationInvite + the public invite ninja API), `teams/` (Team model + ninja API).
- **Settings**: `config/settings/` — `_base.py` (main, env-driven via epicenv), `__init__.py` (re-exports `_base`), `test_runner.py` (overrides for pytest), `e2e.py` (overrides for Playwright with pre-built Vite assets).
- **API**: A single `NinjaAPI` instance in `config/api.py` mounted at `/api/`. Routers come from each app's `api.py` (`apps.base.api`, `apps.accounts.api`, `apps.organizations.api`, `apps.teams.api`).
- **URLs** (`config/urls.py`): A re_path catch-all serves the Vue SPA shell for every non-API path. `/_allauth/` mounts allauth's headless API, `/hijack/` mounts django-hijack, `/admin/` is the Django admin, `/api/` is the ninja API. A `_public_not_found` shim before the catch-all keeps stale `/public/static/*` chunks from being answered with HTML.
- **Frontend**: Vue 3 SPA in `frontend/` (was `src/` pre-conversion). `frontend/js/app.js` mounts `App.vue`, `frontend/js/router.js` defines all SPA routes (lazy-loaded). `frontend/js/stores/app.js` is the reactive app store; `appStore.fetchContext()` hits `/api/app-context/` to populate user, org, organizations, version, etc. `frontend/css/app.css` is Tailwind v4 with Fraunces / IBM Plex Sans / JetBrains Mono via Google Fonts. Built with bun + Vite.
- **Docker**: `compose.yml` with healthchecks on every service: `db` (postgres 17), `redis` (7), `mailpit`, `minio`, `web`, `worker` (celery), `frontend` (bun running Vite). The web container runs `migrate` and `ensure_s3_bucket` on startup. Multi-stage production image at `config/docker/Dockerfile.web` (python-requirements → base → dev / js_assets → prod with gunicorn).
- **Static / media**: WhiteNoise serves Vite-hashed assets in production with `Cache-Control: max-age=31536000, immutable` (regex defined in settings). Media uploads use `apps/base/storage.py:S3MediaStorage` which handles the Docker-internal vs. browser endpoint URL split for MinIO.

## Development Commands

Use Just for all development tasks. Common ones:

**Setup & Management:**
- `just start` - `docker compose up`
- `just start_with_debugpy` - same with debugpy listening on `:5678`
- `just stop` - Stop all services
- `just build` - Rebuild Docker images + clear node_modules + collectstatic
- `just build_frontend` - `bun run build` + collectstatic
- `just clean` - Remove caches, coverage, dist
- `just create_env` - Generate `.env` from the schema in `pyproject.toml`

**Code Quality:**
- `just format` - Format Python (ruff), JS (oxfmt + oxlint), HTML (djlint), justfile
- `just lint` - Run all linters + ty type check + check for missing migrations
- `just pre_commit` - format + lint + test

**Testing:**
- `just test` - pytest (Django + ninja API tests)
- `just test_with_coverage` - pytest --cov, opens HTML report
- `just test_e2e [args]` - `bun run build` then pytest e2e/ with `--ds=config.settings.e2e`. Excluded from `just test` via `--ignore=e2e` in `pyproject.toml`.

**Database:**
- `just db_dump` - pg_dump to `~/Downloads/`
- `just db_restore [dump_file]` - Restore from latest or named dump

**Dependencies:**
- `just upgrade_python_packages` - `uv sync --all-packages --all-extras`
- `just upgrade_node_packages` - `bun update`

## Testing

- pytest with pytest-django.
- Test settings in `config.settings.test_runner`; e2e settings in `config.settings.e2e`.
- Model Bakery for fixtures.
- Django Test Plus for additional helpers.
- pyotp for the TOTP / MFA tests under `apps/accounts/tests/test_mfa_flows.py`.
- Playwright e2e tests under `e2e/` (auth flow, invite flow); `--ignore=e2e` is on `pyproject.toml` `[tool.pytest.ini_options]` so the unit suite stays fast.
- Coverage configuration in `config/coverage.ini`.

## Code Standards

- **Python**: Ruff for formatting + linting (replaces Black/isort). Ty for type checking. Django conventions throughout. Bandit (S) ruleset enabled in Ruff.
- **Ninja**: `[tool.ruff.lint.flake8-bugbear] extend-immutable-calls` includes `ninja.Query/File/Form/Body/Path` so default-arg-with-call patterns don't trip B008.
- **JavaScript / Vue**: Oxlint (`.oxlintrc.json`) for linting + Oxfmt (`.oxfmtrc.json`, Prettier-compatible) for formatting. Both run via `bun run lint-js` / `format-js`. Vue SFC `<script>` blocks are linted; `<template>` blocks are formatted but not linted. 120-char line length.
- **HTML / Django templates**: djLint for formatting and linting.
- **CSS**: Tailwind v4 utilities (no separate Sass/Stylelint pipeline anymore — both were dropped during the SPA conversion).
- **Line Length**: 120 characters for Python and HTML.

## Debugging

The project supports remote debugging with VS Code, PyCharm, LazyVim/Neovim, or any DAP-compatible editor.

**Quick Start:**
1. Start with debugging: `just start_with_debugpy`
2. Wait for "Debugger listening on 0.0.0.0:5678"
3. Attach your debugger

**Important:** Auto-reload is disabled when debugging. Manually restart the server after code changes; use `just start` for normal development with auto-reload.

**VS Code:**
1. Run: `just start_with_debugpy`
2. Press F5 or select "Django: Attach Debugger" from the debug dropdown
3. Set breakpoints and debug your code

**PyCharm:**
1. Configure Docker Compose Python interpreter (Settings → Python Interpreter)
2. Create Django Server run configuration
3. Click Debug — PyCharm handles everything automatically
4. See [docs/debugging.md](docs/debugging.md) for detailed setup

**LazyVim/Neovim:**
- Configure nvim-dap to connect to `localhost:5678`
- The debugger uses the standard Debug Adapter Protocol (DAP)
- See [docs/debugging.md](docs/debugging.md)

**Notes:**
- Debugger listens on port 5678
- Use `just stop` then `just start` to switch back to normal mode
- PyCharm uses native Docker Compose debugging (doesn't require debugpy)

## Environment Configuration

Uses `.env` for local development. Schema is defined in `pyproject.toml` under `[tool.epicenv.variables]`. Generate a new `.env` with `just create_env` (or `uvx epicenv create`).

Key variables:
- `DEBUG=on` for development
- `SECRET_KEY` — auto-generated by epicenv's `url_safe_password` initializer
- `DATABASE_URL` — Postgres connection string
- `SITE_DOMAIN` — defaults to `localhost:8000`. **Use `localhost`, not `127.0.0.1`** — WebAuthn / passkey enrollment rejects bare IPs as Relying Party IDs.
- `ALLOWED_HOSTS` — defaults to `localhost,127.0.0.1`
- `INTERNAL_IPS` — for Django Debug Toolbar
- `USE_DEBUGPY=true` — enable remote debugging
- `MEDIA_S3_*` — MinIO / S3 credentials. `MEDIA_S3_ENDPOINT_URL` is the Docker-internal hostname (`http://minio:9000`); `MEDIA_S3_URL_ENDPOINT_URL` is the browser-facing one (`http://localhost:9000`). The split is handled by `apps.base.storage.S3MediaStorage`.
- `ACCOUNT_SIGNUP_OPEN` — bool, gates new registrations.

## SPA Auth Flow

`HEADLESS_ONLY = True`, so allauth never renders templates — it returns JSON via `/_allauth/browser/v1/...`. The Vue SPA at `frontend/js/accounts/views/*` drives the entire flow:

- **Sign-in**: `LoginView.vue` POSTs to `/_allauth/browser/v1/auth/login`. Honors `?next=` (skipping `/accounts/*` redirects).
- **Sign-up**: `SignupView.vue` POSTs to `.../auth/signup`. Includes a hidden `timezone` field auto-populated by `Intl.DateTimeFormat`. After signup, if email verification is optional and the user is auto-logged-in, honors `?next=`.
- **Email verification**: link in the email goes to `/accounts/confirm-email/{key}` (Vue route via `HEADLESS_FRONTEND_URLS`).
- **Password reset**: 3-step flow under `frontend/js/accounts/views/PasswordReset*View.vue`.
- **MFA**: TOTP, recovery codes, WebAuthn passkeys. The TOTP enrollment QR is rendered locally at `/qr/?data=<otpauth-url>` (login_required) using the `qrcode` package — no third-party image service.
- **Org invite**: email link points to `/organizations/invite/<key>/accept/`, served by `SPAView` via a re_path that keeps the `accept_invite` URL name for `reverse()`. The Vue page (`frontend/js/views/AcceptInviteView.vue`) hits `/api/invite-by-key/<key>/` for the lookup; accept and decline endpoints live on the same prefix.

## Multi-Tenant Scaffolding

- `Organization` (name, slug, billing_email), `OrganizationMember` (with `is_owner` + `is_primary` flags), `OrganizationInvite` (key-based, 7-day expiration).
- `OrganizationMiddleware` lazy-loads `request.org` from the session via `apps.organizations.session`. The session caches a minimal serialized org dict; the full model instance is only fetched when `org.instance` is accessed.
- `apps/organizations/signals.py` switches to the user's primary org on login / hijack-start / hijack-end.
- The org switcher in the AppLayout user menu, the OrgSettingsLayout (General / Members / Teams tabs), and the OrgCreateView/OrgSwitchView pages are SPA-driven; the only server-rendered org URL is the catch-all that gives the SPA the accept-invite path.

## Key Dependencies

- **Backend**: Django 5, django-allauth[mfa] (with fido2 for WebAuthn), django-ninja, django-hijack, Pillow, Celery, Redis, PostgreSQL 17, gunicorn, WhiteNoise, django-storages + boto3, django-ses, django-alive, django-maintenance-mode.
- **Frontend**: Vue 3, Vue Router 5, Tailwind v4, Vite 8, bun, @heroicons/vue, vue-advanced-cropper, reka-ui (modal/toast primitives).
- **Development**: Docker, pytest, pytest-playwright, pyotp, Ruff, Ty, Oxlint, Oxfmt, djLint, model-bakery.
