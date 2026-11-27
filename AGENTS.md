# AGENTS.md

This file provides guidance to coding agents when working with code in this repository.

## Project Overview

Django Base Site is an opinionated Django starter template with a production-ready foundation. The stack is Django 6 + django-ninja + django-allauth (headless mode, with MFA + WebAuthn passkeys) on the backend, and a Vue 3 SPA with Tailwind v4 on the frontend. Multi-tenant scaffolding (organizations, teams, invites), a notifications system (in-app + email, per-user category prefs, generic-target cleanup, retention purge), and an opt-in Stripe billing app (Checkout + Customer Portal, settings-declared plans + features, per-seat pricing, trials, coupons) are built in. Celery + Redis for background tasks, Silo for S3-compatible local media storage, gunicorn in production.

## Architecture

- **Apps**: Under `apps/` — `accounts/` (custom user with timezone + avatar fields), `base/` (utilities, ninja error handlers, storage backends, the SPA shell view, the `qr_svg` view, etc.; it imports no other app), `organizations/` (Organization, OrganizationMember, OrganizationInvite + the public invite ninja API), `teams/` (Team model + ninja API), `notifications/` (Notification + NotificationPreference, ninja API at `/api/notifications/`, `notify()` producer helper, retention purge via celery beat, GenericForeignKey post_delete cleanup driven by `settings.NOTIFICATIONS_TARGET_MODELS`, per-user category prefs declared in `settings.NOTIFICATIONS_CATEGORIES`), `billing/` (opt-in Stripe subscriptions tied to Organizations — see Billing section below), `site/` (the code that uses several apps at once: the app-context, version, impersonation-banner and test-notification endpoints, the `seed` command behind `just seed`, and the `accounts` template tag library). See App Layers for what each app may import.
- **Billing app** (`apps/billing/`, opt-in via `BILLING_ENABLED`): models are `BillingCustomer` + `Subscription` + `WebhookEvent`. Plans + features are declared in `settings.BILLING_PLANS` / `settings.BILLING_FEATURES` and loaded into `apps/billing/plans.py` and `apps/billing/features.py` dataclasses (mirrors the notifications-categories pattern). New subscriptions go through Stripe Checkout (full-page redirect); upgrades/cancels/payment-methods/invoices go through the Stripe Customer Portal. The webhook lives at `/webhooks/stripe/` (registered in `config/urls.py` outside the ninja API because it uses HMAC, not session+CSRF) and dedupes Stripe retries via `WebhookEvent`. Feature gating: `apps.billing.access.org_has_feature(org, key)` and the `requires_feature` decorator return `True`/pass through when `BILLING_ENABLED=False` so the starter template runs out of the box without Stripe credentials. Per-seat sync runs as a `transaction.on_commit` hook from `OrganizationMember` `post_save`/`post_delete`. Trial reminders + drift recovery run as celery beat tasks.
- **Email**: Every email is sent from the Celery `worker`, never in a request or a beat task. `apps.base.utils.email.send_email()`, `apps.notifications.email.send_email()` (the same, minus the users who turned off email for its `category`), and allauth's emails (`AccountAdapter.send_mail`) render the message in the caller, then `queue_email()` hands its strings to `apps.base.tasks.send_email_message`, which retries transport errors (SMTP, socket, SES) with backoff. If the broker can't take the task, the error is logged, not raised. To send a hand-built `EmailMessage`, pass it to `queue_email()` rather than calling `.send()`. The worker doesn't reload code like `runserver` does: restart it (`docker compose restart worker`) after changing a Celery task. Test and e2e settings run tasks eagerly (`CELERY_TASK_ALWAYS_EAGER`), so `mail.outbox` still gets the message. `apps/base/tests/mail.py` has `use_failing_mail_server()` and `record_queued_emails()` for testing a mail outage.
- **Settings**: `config/settings/` — `_base.py` (main, env-driven via epicenv), `__init__.py` (re-exports `_base`), `test_runner.py` (overrides for pytest), `e2e.py` (overrides for Playwright with pre-built Vite assets).
- **API**: A single `NinjaAPI` instance in `config/api.py` mounted at `/api/`. Routers come from each app's `api.py` (`apps.site.api`, `apps.accounts.api`, `apps.organizations.api`, `apps.teams.api`, `apps.notifications.api`, and `apps.billing.api` when `BILLING_ENABLED`).
- **URLs** (`config/urls.py`): A re_path catch-all serves the Vue SPA shell for every non-API path. `/_allauth/` mounts allauth's headless API, `/hijack/` mounts django-hijack, `/admin/` is the Django admin, `/api/` is the ninja API. A `_public_not_found` shim before the catch-all keeps stale `/public/static/*` chunks from being answered with HTML.
- **Frontend**: Vue 3 SPA in `frontend/` (was `src/` pre-conversion). `frontend/js/app.ts` mounts `App.vue`, `frontend/js/router.ts` defines all SPA routes (lazy-loaded) and types their `meta` flags. `frontend/js/stores/app.ts` is the reactive app store, which components read with `useAppStore()`; `appStore.fetchContext()` hits `/api/app-context/` to populate user, org, organizations, version, etc. `frontend/css/app.css` is Tailwind v4 with IBM Plex Sans (for all UI text) and JetBrains Mono (for code) via Google Fonts. Built with bun + Vite.
- **Typed API contract**: The SPA is TypeScript (`frontend/tsconfig.json`, `strict`, no `allowJs`); `apps/base/tests/test_frontend_typescript.py` fails on a `.js` module under `frontend/js/` or a component whose `<script>` isn't `lang="ts"`. `just generate_api_types` exports the ninja and allauth OpenAPI specs under `config.settings.api_types` (no server or database needed) and writes `frontend/js/api/schema.d.ts` and `allauth.d.ts` with `frontend/config/generate-api-types.mjs`, which leaves a request-body field the backend defaults optional and types an object schema with no listed properties as `Record<string, unknown>`. Those files are generated and checked in: never edit them, and regenerate them in the same change as any ninja schema change. `frontend/js/utils/api.ts` exports `api` (openapi-fetch over the generated types, plus a stricter type layer that rejects unknown top-level body keys), `unwrap()`, `ApiError`, `formDataBody` for multipart uploads, and `getAllResults()`, which loads every page of a paginated list. Every ninja route needs a `response=` schema, or its type has no body; `apps/site/tests/test_app_context_api.py` fails on any route without one.
- **Docker**: `compose.yml` services: `db` (postgres 17), `redis` (7), `mailpit`, `silo`, `web`, `worker` (celery), `frontend` (bun running Vite). All but `web` and `worker` have healthchecks. The web container runs `migrate` and `ensure_s3_bucket` on startup. Multi-stage production image at `config/docker/Dockerfile.web` (python-requirements → base → dev / js_assets → prod with gunicorn). Services have no fixed `container_name`, and every port published on the host is a `${HOST_PORT_*:-default}` variable, so a second copy of the stack can run beside the first (see Worktrees); `apps/base/tests/test_compose_file.py` keeps it that way. Use `docker compose` with service names (`docker compose exec web ...`), not container names.
- **Worktrees**: [Worktrunk](https://worktrunk.dev) hooks in `.config/wt.toml` run `scripts/worktree`, so every git worktree gets its own stack: `setup` (pre-start) writes the worktree's `.env` from the main checkout's with its own `COMPOSE_PROJECT_NAME`, free `HOST_PORT_*` ports, and the `SITE_DOMAIN`, `MEDIA_S3_URL_ENDPOINT_URL`, and `SESSION_COOKIE_NAME` that go with them, then copies the main checkout's Postgres and Silo volumes. `teardown` (pre-remove) deletes the worktree's containers, volumes, and network. A worktree of a branch made before this has the old fixed ports and container names, so `setup` skips it until it's rebased onto `main`.
- **Content-Security-Policy**: Django's built-in CSP enforces a policy built by `content_security_policy()` in `config/settings/_base.py`. Loading a script, stylesheet, font, image or API from a new origin means adding it there, and an inline `<script>` in a template needs `nonce="{{ csp_nonce }}"`. Browsers block anything else, so a page that loads one breaks; `e2e/test_content_security_policy.py` fails on any violation, so add a new page to its list. The policy has no `'unsafe-eval'`, so in an e2e test pass Playwright's `wait_for_function` a function (`"n => window.items.length === n"`, with `arg=`), not a bare expression, which it runs through `eval()`.
- **Static / media**: WhiteNoise serves Vite-hashed assets in production with `Cache-Control: max-age=31536000, immutable` (regex defined in settings). Media uploads use `apps/base/storage.py:S3MediaStorage` which handles the Docker-internal vs. browser endpoint URL split for Silo.

## App Layers

Each app imports only the apps below it. `just lint` (`just lint_imports`) checks it with import-linter, using the contracts under `[tool.importlinter]` in `pyproject.toml`. Top to bottom:

| Layer | May import |
| --- | --- |
| `site` | any app. Only code that has to use several apps at once goes here: the app-context endpoint, the `seed` command, test notifications. Nothing imports it except `config/`. |
| `teams` and the other feature apps | `billing` (through `apps.billing.access` only), `notifications`, `organizations`, `accounts`, `base`. Never another feature app. |
| `billing` | `notifications`, `organizations`, `accounts`, `base` |
| `notifications` | `organizations`, `accounts`, `base` |
| `organizations` | `accounts`, `base` |
| `accounts` | `base` |
| `base` | no other app: utilities, error handlers, storage, the SPA shell, email sending |

- **Billing**: other apps import only `apps.billing.access` (`org_has_feature`, `requires_feature`, `org_billing_summary`, `BillingSummaryOut`), so billing's models, Stripe calls and webhooks can change without touching them. `config/` still mounts billing's router and webhook; it sits above every app and isn't checked.
- **The checks count every import**: one inside a function, one under `TYPE_CHECKING`, and the tests'. The one exception: `apps.base.tests` may import `accounts` and `organizations`, because `BaseTest` and the `sign_in` helpers sign a user in and select their organization.
- **A new app** has to be placed in the layers contract, or `just lint` fails (`exhaustive = true`). A feature app goes on teams' line (`"teams | projects"`), which also keeps the two from importing each other.
- **When a lower app needs something from a higher one**, move the code to the app that owns it: the organization permission checks live in `apps/organizations/permissions.py`, next to the roles they check, and email filtered by notification category is `apps.notifications.email.send_email`, not a branch in `apps.base`. Code that has to use several apps at once goes up to `site`. Don't add an `ignore_imports` entry to make a contract pass.

## Development Commands

Use Just for all development tasks. Common ones:

**Setup & Management:**
- `just init` - First-time setup: brings services up, runs `just create_superuser`, then attaches — use on a new project's first boot or after wiping the DB. Use `just start` for every subsequent boot.
- `just start` - `docker compose up`
- `just start_with_debugpy` - same with debugpy listening on `:5678`
- `just stop` - Stop all services
- `just doctor` - Read-only check that the stack in front of you is this checkout's and is ready to drive: the checkout, its Compose project and URLs, each service's state and health, the app and Vite answering, pending migrations, and whether `just seed` has run. Exits non-zero and names the fix. Run it before driving the app (`scripts/doctor`).
- `just build` - Rebuild Docker images + clear node_modules + collectstatic
- `just build_frontend` - `bun run build` + collectstatic
- `just clean` - Remove caches, coverage, dist
- `just create_env` - Generate `.env` from the schema in `.env.toml`
- `just create_superuser` - Idempotent `epicenv create-superuser` (edit the recipe in the top-level `justfile` to pipe credentials from a secrets manager)
- `just seed` - Known dev logins cast from The Office and Parks and Rec (password `dev-password`; the superuser is the `DJANGO_SUPERUSER_*` account in `.env`), two orgs, teams, and pending + expired invites. DEBUG and a local database only; safe to rerun. It resets the seeded logins' passwords and removes their MFA, but otherwise never deletes what you created by hand. Prints the logins and invite accept URLs.

**Code Quality:**
- `just format` - Format Python (ruff), JS (oxfmt + oxlint), HTML (djlint), justfile
- `just lint` - Run all linters + the app import contracts (see App Layers) + ty type check + check for missing migrations + Django's deployment checks + check the generated API types are current + vue-tsc
- `just lint_deploy` - `manage.py check --deploy --fail-level WARNING` under `config.settings.deploy_check`, with DEBUG off and no `.env`, so the production HTTPS defaults can't quietly regress. It silences only `security.W005` and `security.W021` (HSTS `includeSubDomains` and `preload`, which each project decides for its own domain); `check --deploy` in a real deploy still shows them.
- `just generate_api_types` - Regenerate `frontend/js/api/*.d.ts` from the ninja and allauth OpenAPI specs; run it after changing a ninja schema and commit the result
- `just verify` - lint, then pytest with `-x --ff -q` (stops at the first failure, last run's failures first), then `just test_js`; run it before calling work done
- `just pre_commit` - format + lint + test + test_js + test_e2e

**Testing:**
- `just test` - pytest (Django + ninja API tests)
- `just test_js` - Vitest for the SPA's unit and component tests (`frontend/js/**/*.test.ts`)
- `just test_with_coverage` - pytest --cov, opens HTML report
- `just test_e2e [args]` - `bun run build` then pytest e2e/ with `--ds=config.settings.e2e`. Excluded from `just test` via `--ignore=e2e` in `pyproject.toml`.

**Database:**
- `just db_dump` - pg_dump to `~/Downloads/`
- `just db_restore [dump_file]` - Restore from latest or named dump

**Dependencies:**
- `just upgrade_python_packages` - `uv sync --all-packages --all-extras`
- `just upgrade_node_packages` - `bun update`

<!-- template-only:start -->

**Documentation:**
- Documentation is built with [Zensical](https://zensical.org/) (successor to MkDocs + Material).
- `just docs` - Serve docs locally at http://localhost:4000
- `just docs-build` - Build the static site (outputs to `docs_site/`)
- `just docs-lint` - Check links in the documentation
- Config: `zensical.toml` (at project root); the recipes live in `config/docs.just`
- The old `docker compose --profile docs` service has been removed.

<!-- template-only:end -->
**Worktrees** (needs [Worktrunk](https://worktrunk.dev), `wt`):
- `wt switch --create <branch>` - New worktree with its own `.env`, ports, and a copy of the main checkout's database and media. Then `just start` there. Worktrunk's default puts it beside the main checkout, at `../<repo>.<branch>`.
- `wt remove <branch>` - Remove the worktree's containers, volumes, and network, then the worktree. `wt merge` does the same.
- `scripts/worktree urls` - This checkout's URLs and ports. Read them from here; never assume `localhost:8000` in a worktree. In a worktree that was never set up (its `.env` has no `HOST_PORT_WEB`), it fails and says to run `scripts/worktree setup`, because the default ports are the main checkout's and its stack would answer in place of this one's.
- `scripts/worktree teardown && scripts/worktree copy-data` - Replace the worktree's database and media with a fresh copy of the main checkout's.
- Create worktrees with `wt`, not `git worktree add`, so the hooks run. For one made another way, run `scripts/worktree setup` inside it.
- Claude Code's own worktrees (`claude --worktree`, subagents with `isolation: "worktree"`) go through `wt` too: `.claude/settings.json` enables [Worktrunk's Claude Code plugin](https://worktrunk.dev/claude-code/), whose `WorktreeCreate` and `WorktreeRemove` hooks run `wt switch --create` and `wt remove` in place of `git worktree add`. Claude Code offers to install it the first time it opens the project. Without `wt` installed, those worktrees fail to create rather than skip setup. The Claude desktop app makes its worktrees itself and skips the plugin, so run `scripts/worktree setup` in one of those.
- The hooks need approving once per machine: `wt config approvals add` in the main checkout (it prompts), or answer the prompt on the first `wt switch --create`. In a shell that can't prompt, `wt` stops with "Cannot prompt for approval" and creates nothing. Ask the user to approve them rather than passing `--yes` for them.

**Claude Code permissions:** `.claude/settings.json` (checked in) makes Claude Code refuse commands that destroy local data, such as `docker compose down -v`, `manage.py flush`, and `migrate --fake`, and ask before `just db_restore`, `scripts/worktree teardown`, `wt remove`, a force push, or dropping a database. The rules match the command as written, so they catch the usual spellings, not every one. Personal settings go in `.claude/settings.local.json`, which git ignores; it can add rules but can't lift these, because a deny or ask rule in any settings file wins over an allow.

## Testing

- Run `just verify` before calling work done. It doesn't run the e2e suite, so also run `just test_e2e` when a change touches the SPA or a flow the e2e tests cover.
- pytest with pytest-django. Database test classes subclass `BaseTest` (`apps/base/tests/_base.py`), Django's `TestCase` plus a `sign_in` method. Test data comes from each app's recipes (see Test Data). Test settings are `config.settings.test_runner`; e2e settings are `config.settings.e2e`. Coverage configuration is in `config/coverage.ini`.
- Playwright e2e tests are under `e2e/`. `--ignore=e2e` in `pyproject.toml`'s `[tool.pytest.ini_options]` keeps them out of `just test`.
- Vitest (run by `just test_js`) unit-tests the SPA's TypeScript and components. Put a test beside its module as `<name>.test.ts` and import `describe`, `test`, `expect` (and `vi` for mocks) from `vitest`. It runs under happy-dom with the Vite config's `@` alias; mount a component with `mount()` from `@vue/test-utils`.
- `frontend/js/utils/api.type-test.ts` holds type-level regression tests: `@ts-expect-error` lines for API bugs that shipped before the types existed, next to the same calls written correctly. `vue-tsc` fails if one stops being an error. Add one when the types should have caught a bug.
- pyotp for the TOTP / MFA tests under `apps/accounts/tests/test_mfa_flows.py`. Turn on two-factor authentication with `make_totp(user)` (`apps/accounts/recipes.py`), which returns the secret. Make a code with `current_totp_code(secret)` from `apps/accounts/tests/totp.py`, not `pyotp.TOTP(secret).now()`: allauth accepts only the current 30-second window's code, so the helper waits out a window's last 5 seconds rather than make a code that expires before the server checks it.
- Every `apps.*` management command must import cleanly; `apps/base/tests/test_management_commands.py` loads them all, since `ty` ignores unresolved imports.
- To check a UI change in the browser, follow the `run-app` skill ([.agents/skills/run-app/SKILL.md](.agents/skills/run-app/SKILL.md)): start the stack, `just seed`, `just doctor`, then sign in as a seeded login with Playwright. Its feature map (`.agents/skills/run-app/features/`) leads from a bug report or a screenshot to the feature's routes, login, steps and e2e tests. Given a bug report, follow the `fix-bug` skill ([.agents/skills/fix-bug/SKILL.md](.agents/skills/fix-bug/SKILL.md)): reproduce it in the running app and report reproduced, not reproduced, or already fixed on `main`, with evidence, before changing code, then fix it under a test that fails first.
- CI (`.github/workflows/ci.yml`) runs `just lint`, `just test_js`, the pytest suite, and the Playwright e2e suite on pushes to `main` and on pull requests. All three jobs run on the runner, not in the compose containers: they install Python packages with `astral-sh/setup-uv`, whose cache makes that take seconds, set `PYTHON_CMD_PREFIX`, `PYTHON_CMD_PREFIX_WITH_DEPS` and `BUN_CMD_PREFIX` to empty, and use a Postgres service container. The E2E job installs Playwright's Chromium with `playwright install chromium --with-deps`. Building the web image took 3–6 minutes whenever `uv.lock` changed, so only the Template workflow builds and boots the images. Both pytest steps run on every core with pytest-xdist (`-n auto`) and print their 15 slowest tests (`--durations=15`); pass `-n 4` to `just test_e2e` to do the same locally. Dependabot (`.github/dependabot.yml`) opens weekly dependency PRs; the `/weekly-maintenance` skill reviews and merges them.
- Workflows install `just` with `extractions/setup-just`, not the `just.systems` install script, which fails on GitHub's API rate limit. Pin every action to a full commit SHA with its release in a trailing comment (`uses: actions/checkout@<sha> # v7.0.1`), as GitHub's hardening guide recommends; Dependabot updates both.

### Choosing a Layer

Test each behavior once, at the cheapest layer that can observe it faithfully:

- **Vitest, no mounting:** a plain TypeScript function or composable (state changes, data transforms, API coordination, router guard decisions). When logic in a component is hard to test, move it into a composable or a `utils/` function and test that.
- **Vitest + `@vue/test-utils`:** a component whose rendered output, ARIA attributes or emits are its contract, such as `FormField` or `AppModal`. Don't mount a whole view to reach logic a composable test could cover.
- **pytest with the Django test client:** server behavior, such as permissions, validation and its error messages, response shapes, emails, and redirects the server decides.
- **Playwright:** only what needs a real browser: wiring across components and the API, router navigation, CSP enforcement, WebAuthn, focus, scroll and layout, and the file chooser. Keep one representative browser test per flow; cover its cases and permission matrix at a cheaper layer.

### Test Data

- A test class that touches the database subclasses `BaseTest` (`apps.base.tests`) and builds the rows its tests share once, in `setUpTestData`. A test builds only the rows it alone needs. `apps/base/tests/test_sign_in.py` is the example to copy.
- Each test rolls back to a savepoint, and Django gives it its own copy of every attribute `setUpTestData` set, so a test can change shared rows and objects freely. What a rollback doesn't undo stays changed: caches, files in storage, module globals, and signal connections. Undo those in the test.
- `setUpTestData` runs before any per-test fixture. A setting that must hold while the class data is built goes on the class (`@override_settings(...)`); a patch goes in `setUpClass` with `cls.enterClassContext(...)` before `super().setUpClass()`. Reach the `settings`, `monkeypatch`, `caplog` and other pytest fixtures a test body needs through an autouse fixture on the class that stores them on `self`.
- Build data with the recipes in `apps/<app>/recipes.py`: `make_user`, `make_superuser` and `make_totp` (accounts), `make_org`, `make_member` and `make_invite` (organizations), `make_team` (teams), and the billing and notifications recipes. e2e fixtures use them too. When a test needs a kind of object no recipe makes, add a recipe rather than build it inline in a second file.
- Recipes live in app code, not under `tests/`, because `just seed` uses some of them (`make_user`, `make_superuser`, `make_org`, `make_member`, `make_invite`, `make_team`) and a management command can't import from a test package. Each creates a new row unless passed `update=True`, which the seed command passes so it can rerun: the row is looked up and given the recipe's values. Tests never pass it, so building the same row twice fails instead of changing a row another test shares. A change to what a seeded row looks like goes in the recipe, not in `seed.py`.
- Build only the graph the assertions need, and give negative controls explicit values that can't match by chance.
- Don't assert a fixed query count. To catch a query per row, use `BaseTest.assert_queries_dont_grow(url, add_rows)`, which compares the count before and after adding rows (see Adding a Feature).
- A test that doesn't touch the database is a plain `class TestX:` with no DB mark. No module-level test functions, and use bare `assert`, never `self.assertEqual` and the like (Ruff's `PT009` and `PT027`). `apps/base/tests/test_test_style.py` fails on a module-level test function or a `django_db` mark under `apps/`.
- Cases: a `BaseTest` class loops over them with `self.subTest(...)`, since pytest can't parametrize a `TestCase`. A plain class uses `@pytest.mark.parametrize` when each case needs fresh setup, and pytest's `subtests` fixture when the cases share one.
- CI runs tests in parallel (pytest-xdist), so each worker runs a different subset in a different order. A test can't count on another having run first, such as one that loads the URLconf or connects a signal.
- Every e2e test is transactional (`live_server` flushes the database after each one), so `setUpTestData` doesn't apply there. Build its data with recipes in fixtures, starting from `e2e/conftest.py`'s `user` and `org`.

### Signing In

- Only tests of signing in itself sign in through allauth (`api_sign_in(client, email)` in `apps/base/tests/sign_in.py`) or the form (e2e).
- Every other Python test uses `self.sign_in(user, org=None)` on `BaseTest` (for another client, `sign_in(client, user, org)` from `apps/base/tests/sign_in.py`), which force-logs in, selects `org` (default: the user's primary organization) in the session, and records a password sign-in so allauth doesn't ask for the password again before adding a passkey or setting up two-factor authentication.
- Every other e2e test uses the `sign_in` fixture, `sign_in(user, "/path/", org=None)`: it builds the same session and hands the browser its cookie, so the first page the browser loads is the one under test.

### Consolidating Tests

- Put scenarios that share expensive setup and can't break each other in one test, each in a labeled subtest. Keep a separate test when one scenario's writes would break another, or when a later step needs an earlier one to have passed.
- Keep every assertion when merging or moving tests, including the inverse: that what shouldn't change or match didn't. A pull request that moves or deletes a test names the test that covers it now.
- CI prints the 15 slowest tests of each pytest run (`--durations=15`). Check them before adding a slow test.

<!-- template-only:start -->

## Template-Only Files

These exist only in the Django Base Site template. `scripts/start_new_project` runs `just clean_extra_files`, which deletes them from new projects:

- `README.md`, `CHANGELOG.md`, `LICENSE.md`, `docs/`, `zensical.toml`, `config/docs.just`, `.readthedocs.yaml`, `scripts/start_new_project`.
- `config/template.just`, which holds `clean_extra_files` itself, so the recipe doesn't linger in new projects.
- The docs site's dev dependencies (`zensical`, `mkdocs-linkcheck`), removed from `pyproject.toml` and `uv.lock` with `uv remove`.
- `.github/workflows/template.yml` — the "Tests install script" job: runs `scripts/start_new_project` and checks the generated project (CI and Dependabot kept, docs tooling and its dependencies gone, no dead links or `just` recipes in its AGENTS.md, nothing else pointing at the deleted files, images pullable, `.claude/settings.json` committed and `.claude/settings.local.json` ignored), checks `scripts/worktree urls` works before `git init` and refuses a worktree made with `git worktree add`, then boots it with `docker compose up`, checks `/api/app-context/` responds, checks `just doctor` fails before `just seed` (naming it), runs `just seed` twice, signs in as a seeded login and as the superuser from the generated `.env`, and checks `just doctor` then passes and refuses the unset-up worktree. It doesn't run pytest; `ci.yml`'s Tests job covers the code. It's the only job that builds the Docker images. A pull request runs it only when it touches a path in the workflow's `paths` list (the installer, the files it edits, the images and compose stack, and what `just seed` runs), and every push to `main` runs it; add a path there when this job starts checking something new.
- Blocks of this file wrapped in `<!-- template-only:start -->` / `<!-- template-only:end -->` markers, each on a line of its own. Put anything that only applies to the template (docs site, release notes, the install script) inside such a block, and don't link to the files above from outside one.

<!-- template-only:end -->
## Code Standards

- **Python**: Ruff for formatting + linting (replaces Black/isort). Ty for type checking. Django conventions throughout. Bandit (S) ruleset enabled in Ruff.
- **Ninja**: `[tool.ruff.lint.flake8-bugbear] extend-immutable-calls` includes `ninja.Query/File/Form/Body/Path` so default-arg-with-call patterns don't trip B008.
- **JavaScript / Vue**: Oxlint (`.oxlintrc.json`) for linting + Oxfmt (`.oxfmtrc.json`, Prettier-compatible) for formatting. Both run via `bun run lint-js` / `format-js`. Vue SFC `<script>` blocks are linted; `<template>` blocks are formatted but not linted. 120-char line length.
- **TypeScript**: Write modules as `.ts` and components with `<script setup lang="ts">`, typing props and emits with `defineProps<...>()` and `defineEmits<...>()`. `vue-tsc` checks both, templates included. Narrow a nullable value (`appStore.user`, `appStore.org`) with `v-if`, optional chaining, or a computed rather than a `!` assertion or an `as` cast. Oxlint bans `any` (`typescript/no-explicit-any`); use `unknown` and narrow it. Call the API with `api` and `unwrap()`, passing the path template and its params (`api.GET('/api/teams/{team_id}/', { params: { path: { team_id } } })`), never a URL built with a template literal, and pass request bodies inline so unknown keys are caught. A caught error is `unknown`: check `err instanceof ApiError` before reading `err.response.status` or `err.data`. Take types from `components['schemas']` in `@/api/schema` rather than redeclaring them.
- **Form fields**: Use `FormField` (`frontend/js/accounts/components/FormField.vue`), which ties its label and its errors to the input. A field built by hand needs a `<label for>`, and while it shows an error, `aria-invalid="true"` and `aria-describedby` naming the error's element. `e2e/test_form_labels.py` and `e2e/test_form_errors.py` check each form.
- **HTML / Django templates**: djLint for formatting and linting.
- **CSS**: Tailwind v4 utilities (no separate Sass/Stylelint pipeline anymore — both were dropped during the SPA conversion).
- **Line Length**: 120 characters for Python and HTML.
- **UI copy**: Labels are Title Case. That covers headings, page and modal titles, buttons (including an icon button's `aria-label` and its loading text), action links, nav and tab items, form labels, table headers, chips, badges, and select options. Keep articles, coordinating conjunctions, and prepositions of four letters or fewer (a, an, the, and, but, or, of, in, on, to, for, at, by, with, from) lowercase unless they come first or last. Capitalize the particle of a phrasal verb ("Sign In", "Set Up") and both halves of a hyphenated compound ("Two-Factor", "In-App"). Package and product names keep their own casing (`django-allauth`, `bun`, `Tailwind v4`). Examples: "Sign In with a Passkey", "Read the Docs", "Teams Aren't Included on Your Current Plan". Sentence case is for sentences and hints: descriptions, subtitles, help text, placeholders, tooltips, empty states, toasts, confirmations, error messages, greetings, and checkbox labels that read as a sentence. Django admin strings (model `verbose_name`s and choice labels) follow Django's own sentence-case convention.

## Fixes and Pull Requests

- **A bug fix comes with its regression test**, in the same pull request: a test or CI check that fails on the old code and passes with the fix. Run it against the old code to see it fail. The `fix-bug` skill ([.agents/skills/fix-bug/SKILL.md](.agents/skills/fix-bug/SKILL.md)) walks through it.
- **When a linter flags code, change the code.** That includes a linter upgrade that adds rules: rewrite what it flags rather than add an ignore to make it pass. A suppression that's still needed names its rule and says why on the same line: `# noqa: S105 (a placeholder, never sent anywhere)`, `// oxlint-disable-next-line no-console -- logs the origin and RP ID ...`, `# ty: ignore[rule]`. Ruff fails on a `noqa` or `type: ignore` with no rule code (`PGH004`, `PGH003`) and on a `noqa` that suppresses nothing (`RUF100`); Oxlint fails on an unused disable comment.
- **One logical change per pull request.** Its description says what changed and why, and names the regression test. A pull request that moves or deletes a test names the test that covers it now (see Testing).

### When a Review Comment Repeats, Make It a Check

A rule that's only written here gets applied unevenly; a red CI run doesn't. When the same comment comes up in review twice, turn it into the cheapest check that can catch it:

- **A Ruff or Oxlint rule**, when one exists: add it to `select` in `pyproject.toml` or to `.oxlintrc.json`, and fix what it flags.
- **A guard test in `apps/base/tests/`** (or `apps/site/tests/`, when it has to import several apps) for a project rule no linter knows, reading the code or config it guards. `test_frontend_typescript.py`, `test_env_schema.py`, `test_compose_file.py` and `apps/site/tests/test_app_context_api.py` are examples.
- **A `@ts-expect-error` line in `frontend/js/utils/api.type-test.ts`** for an API call the types should reject.
- **An e2e test** for what only shows in a browser, such as `e2e/test_content_security_policy.py` and `e2e/test_form_labels.py`.

Then shorten the prose here to the rule and the check that enforces it. Don't write a test that greps a CI workflow's YAML: say what the workflow does in this file instead.

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
4. See the [debugging guide](https://django-base-site.readthedocs.io/en/latest/debugging/) for detailed setup

**LazyVim/Neovim:**
- Configure nvim-dap to connect to `localhost:5678` (`HOST_PORT_DEBUGPY` in a worktree's `.env`)
- The debugger uses the standard Debug Adapter Protocol (DAP)
- See the [debugging guide](https://django-base-site.readthedocs.io/en/latest/debugging/)

**Notes:**
- Debugger listens on port 5678
- Use `just stop` then `just start` to switch back to normal mode
- PyCharm uses native Docker Compose debugging (doesn't require debugpy)

## Environment Configuration

Uses `.env` for local development. Schema is defined in `.env.toml` under `[variables]`. A variable's `default` is a value of its type (`false`, not `"false"` or a description), the one it has in a generated `.env`, where DEBUG is on. epicenv uses it only for that `.env` and `epicenv diff`; the runtime default is in the settings. When it depends on DEBUG, say so in `help_text`. `apps/base/tests/test_env_schema.py` checks the types. Generate a new `.env` with `just create_env` (or `uvx epicenv create`).

Key variables:
- `DEBUG=on` for development
- `SECRET_KEY` — auto-generated by epicenv's `url_safe_password` initializer
- `DATABASE_URL` — Postgres connection string
- `SITE_DOMAIN` — defaults to `localhost:8000`. **Use `localhost`, not `127.0.0.1`** — WebAuthn / passkey enrollment rejects bare IPs as Relying Party IDs.
- `HOST_PORT_WEB` / `_VITE` / `_DB` / `_SILO` / `_SILO_CONSOLE` / `_MAILPIT` / `_MAILPIT_SMTP` / `_DEBUGPY` — the host ports `compose.yml` publishes (defaults 8000, 3000, 5432, 9000, 9001, 8025, 1025, 5678). Unset in the main checkout; `scripts/worktree setup` sets them in a worktree's `.env`, with `COMPOSE_PROJECT_NAME`, a matching `SITE_DOMAIN` and `MEDIA_S3_URL_ENDPOINT_URL`, and `SESSION_COOKIE_NAME` (browsers share cookies across ports, so each stack needs its own session cookie). Django reads `HOST_PORT_VITE` as `VITE_SERVER_PORT`.
- `ALLOWED_HOSTS` — defaults to `localhost,127.0.0.1`
- `SECURE_SSL_REDIRECT` / `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` / `SECURE_HSTS_SECONDS` — HTTPS. Each is on by default when DEBUG is off (HSTS for one year, for this host only) and off when it's on, so production needs none of them set, only HTTPS in front of the app. Turn them off (`off`, or `SECURE_HSTS_SECONDS=0`) only for a deploy without TLS, such as a staging site. Behind a proxy that terminates TLS, Django has to see requests as HTTPS or the redirect loops: `gunicorn.conf.py` trusts the proxy's `X-Forwarded-Proto` (`forwarded_allow_ips`), and `SECURE_PROXY_SSL_HEADER=on` makes Django trust it under any other server. django-alive's `/-/alive/` and `/-/health/` are never redirected. `SECURE_HSTS_INCLUDE_SUBDOMAINS` and `SECURE_HSTS_PRELOAD` stay off until a project turns them on for its own domain. The test and e2e settings pin all of these off, because the test client and the live server speak plain HTTP and CI runs both with DEBUG off.
- `INTERNAL_IPS` — for Django Debug Toolbar, which is off until you turn it on with **Debug Toolbar** in the user menu (DEBUG only). The choice is a `debug_toolbar` cookie read by `apps/base/debug_toolbar.py`, not a setting.
- `USE_DEBUGPY=true` — enable remote debugging
- `MEDIA_S3_*` — Silo / S3 credentials (locally they are also Silo's root user and password). `MEDIA_S3_ENDPOINT_URL` is the Docker-internal hostname (`http://silo:9000`); `MEDIA_S3_URL_ENDPOINT_URL` is the browser-facing one (`http://localhost:9000`). The split is handled by `apps.base.storage.S3MediaStorage`.
- `ACCOUNT_SIGNUP_OPEN` — bool, gates new registrations.
- `SENTRY_DSN` — reports errors from Django and Celery to Sentry, tagged with `INSTANCE` as the environment; blank (the default) turns it off. `apps/base/sentry.py` starts it from `BaseConfig.ready()` rather than from settings, so the test, e2e, `api_types` and `deploy_check` settings can set `SENTRY_DSN = ""` and never report, even with a DSN in `.env`. Events leave out who the user is, their IP address (`X-Forwarded-For` included), cookies, request bodies (`max_request_body_size="never"`), and the values of local variables in a stack trace (`include_local_variables=False`); `apps/base/tests/test_sentry.py` checks that. Sentry filters local variables only by name, such as password or token, so a view's locals would send what people typed, such as an invited email address. A project can turn them on in `apps/base/sentry.py` for more context, knowing that. The SDK reads `SENTRY_RELEASE` from the environment itself.
- `DJANGO_SUPERUSER_USERNAME` / `_EMAIL` / `_PASSWORD` — the superuser. `just create_env` fills them from the 1Password item `op://Private/django-admin` when the `op` CLI is signed in, and otherwise with fallbacks (`admin` / `admin@example.com` / `dev-password`; see `.env.toml`). `just create_superuser` (which `just init` runs on first boot) creates the account via the idempotent `epicenv create-superuser` and skips when they're blank; `just seed` makes the same account its superuser and refuses when they're blank. For production, edit the `just create_superuser` recipe in the top-level `justfile` to pipe credentials from a secrets manager instead of putting them in `.env`.

## SPA Auth Flow

`HEADLESS_ONLY = True`, so allauth never renders templates — it returns JSON via `/_allauth/browser/v1/...`. The Vue SPA at `frontend/js/accounts/views/*` drives the entire flow:

- **Sign-in**: `LoginView.vue` POSTs to `/_allauth/browser/v1/auth/login`. Honors `?next=` (skipping `/accounts/*` redirects).
- **Session expiry**: a 401 from `/api/` while the SPA thinks someone is signed in means their session ended. `app.ts` (through `onUnauthorized()` in `frontend/js/utils/api.ts` and `utils/sessionExpiry.ts`) then loads `/accounts/login/?next=<the page>&session=expired`, and `LoginView.vue` says the session ended. A 401 from `/_allauth/` never counts: allauth sends one on purpose while a two-factor code is pending and after signing out.
- **Sign-up**: `SignupView.vue` POSTs to `.../auth/signup`. Includes a hidden `timezone` field auto-populated by `Intl.DateTimeFormat`. After signup, if email verification is optional and the user is auto-logged-in, honors `?next=`.
- **Email verification**: link in the email goes to `/accounts/confirm-email/{key}` (Vue route via `HEADLESS_FRONTEND_URLS`).
- **Password reset**: 3-step flow under `frontend/js/accounts/views/PasswordReset*View.vue`.
- **MFA**: TOTP, recovery codes, WebAuthn passkeys. The TOTP enrollment QR is rendered locally at `/qr/?data=<otpauth-url>` (login_required) using the `qrcode` package — no third-party image service.
- **Org invite**: email link points to `/organizations/invite/<key>/accept/`, served by `SPAView` via a re_path that keeps the `accept_invite` URL name for `reverse()`. The Vue page (`frontend/js/views/AcceptInviteView.vue`) hits `/api/invite-by-key/<key>/` for the lookup; accept and decline endpoints live on the same prefix.

## Multi-Tenant Scaffolding

- `Organization` (name, slug, billing_email), `OrganizationMember` (with a `role` and an `is_primary` flag), `OrganizationInvite` (key-based, 7-day expiration, with the `role` the invitee gets).
- **Roles and permissions** live in `apps/organizations/roles.py`. A member's `role` (`owner` or `member`) grants the `OrgPerm` permissions listed in `ROLE_PERMISSIONS`. Check permissions, never roles: `require_org_perm(request, OrgPerm.MANAGE_MEMBERS)` in a ninja route, `has_org_perm(user, org, perm)` elsewhere, `org.members_with_perm(perm)` to pick who gets an email, and `appStore.can('manage_members')` in the SPA. Giving, changing or removing a role takes every permission that role grants (`can_assign_role`), so a role with `manage_members` but not billing can't make an owner. App-context reads the current org's `role` and `permissions` from the database on every load, so a role change applies at once. Each org settings tab names its permission in `frontend/js/utils/orgSettings.ts`. To add a permission, add it to `OrgPerm`, grant it in `ROLE_PERMISSIONS`, check it, and run `just generate_api_types`. To add a role, also add a migration for the field's new choice and a badge label in `ManageOrganizationApp.vue` (`vue-tsc` fails without one).
- `OrganizationMiddleware` lazy-loads `request.org` from the session via `apps.organizations.session`. The session caches a minimal serialized org dict (never the user's role); the full model instance is only fetched when `org.instance` is accessed.
- `apps/organizations/signals.py` switches to the user's primary org on login / hijack-start / hijack-end.
- The org switcher in the AppLayout user menu, the OrgSettingsLayout (General / Members / Teams tabs), and the OrgCreateView/OrgSwitchView pages are SPA-driven; the only server-rendered org URL is the catch-all that gives the SPA the accept-invite path.

## Adding a Feature

Copy `apps/teams/` (about 190 lines): an organization-scoped model, its admin, a ninja router, and a settings tab in the SPA (`frontend/js/views/settings/TeamsView.vue` and `frontend/js/apps/ManageTeamsApp.vue`). Write its tests the way the Testing section describes; `apps/base/tests/test_sign_in.py` is a short example. A feature usually needs each of these:

- **App and model**: add the app to `INSTALLED_APPS` in `config/settings/_base.py`, and to the feature layer in `pyproject.toml`'s layers contract, beside teams (`"teams | yourapp"`; see App Layers). Give the model a `ForeignKey` to `organizations.Organization` and a queryset built on `FilterByOrganizationMixin` (`apps/organizations/managers.py`), and read rows through `.filter_by_org(request)` so one organization never sees another's. `just lint` fails on a missing migration.
- **Who can call it**: start each ninja route with `require_org_perm(request, OrgPerm.X)` (`apps/organizations/permissions.py`) for an action a role grants, or `require_org_selected(request)` for one any member can take. Outside a route, use `has_org_perm(user, org, perm)`. A new kind of action gets its own `OrgPerm` (see Multi-Tenant Scaffolding).
- **Schemas**: every route needs a `response=` schema. Check input in the schema, or with the model's `clean_fields()`, so a bad value gets a field error rather than a 500. Teams does both: `TeamIn` trims spaces from the name, and `_save_team` in `apps/teams/api.py` runs `clean_fields()` and turns a name already in use into a field error.
- **Router**: register it in `config/api.py` with `api.add_router(...)`, then run `just generate_api_types` and commit `frontend/js/api/*.d.ts`.
- **SPA**: add the page to `frontend/js/router.ts`. Give it a file in the `run-app` skill's feature map (`.agents/skills/run-app/features/`), or a section in one, laid out as its README describes: its route names and how to reach them, the login and data it needs, a representative flow, its pitfalls, how to clean up after it, and its source and tests, with each e2e test named by its pytest node ID (`e2e/test_x.py::TestClass::test_y`). `apps/base/tests/test_feature_map.py` fails on a route no feature file names, and on a path or e2e test a file names that doesn't exist. An organization settings tab also goes in `TABS` in `frontend/js/utils/orgSettings.ts`, with the permission it takes. Show controls with `appStore.can(perm)`.
- **Notifications**: a model that `notify(..., target=obj)` points at goes in `NOTIFICATIONS_TARGET_MODELS` (`"app_label.ModelName"`), so deleting a row deletes its notifications. A new kind of notification gets a category in `NOTIFICATIONS_CATEGORIES`.
- **Paid features**: declare the feature in `BILLING_FEATURES`, decorate the route with `requires_feature("key")` (`apps/billing/access.py`), and wrap the UI in `FeatureGate` or `useFeature()`. All of them let everything through when `BILLING_ENABLED` is off.
- **Settings**: read each new setting with `env(...)` in `config/settings/_base.py` and declare it in `.env.toml` (see Environment Configuration). `apps/base/tests/test_env_schema.py` fails on one that's read but not declared.
- **Tests**: `BaseTest` classes with `setUpTestData` and recipes under `apps/<app>/tests/` (see Testing), Vitest tests for new components and composables, and an e2e test under `e2e/` for a new page or flow. A new list endpoint also gets a test in `apps/site/tests/test_list_queries.py`, listed in its `LISTS_TESTED`: `assert_queries_dont_grow(url, add_rows)` fails when more rows take more queries, a query per row that `select_related` or `prefetch_related` would fix. The rows it adds have to use each relation the endpoint shows. The same file fails on a list route with no such test. Run `just verify`, and `just test_e2e` when the SPA changed.

## Key Dependencies

- **Backend**: Django 6, django-allauth[mfa] (with fido2 for WebAuthn), django-ninja, django-hijack, Pillow, Celery, Redis, PostgreSQL 17, gunicorn, WhiteNoise, django-storages + boto3, django-ses, django-alive, django-maintenance-mode, sentry-sdk.
- **Frontend**: Vue 3, Vue Router 5, Tailwind v4, Vite 8, bun, openapi-fetch, @heroicons/vue, vue-advanced-cropper, reka-ui (modal/toast primitives).
- **Development**: Docker, pytest, pytest-playwright, pyotp, Ruff, Ty, Oxlint, Oxfmt, djLint, TypeScript, vue-tsc, openapi-typescript.
