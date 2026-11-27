# Feature map

One file per user-facing feature, so a bug report, even a vague one or just a screenshot, leads to the right screen, route, login and steps. Read this file, then only the feature files your task needs. A journey that crosses features is in [cross-cutting-flows.md](cross-cutting-flows.md). The [`fix-bug` skill](../../fix-bug/SKILL.md) starts from here to reproduce a bug and fix it.

Each feature file covers, as far as its feature needs:

1. **Routes:** the routes and how to reach them.
2. **Login and data:** the login, permissions, settings and data the feature needs.
3. **A representative flow**, with what to expect at each step. It names the text to select and wait for in that flow, not every message on the page; the view's source has the rest.
4. **Pitfalls and known issues:** browser behavior that gets in the way, and the app's known bugs, each with its workaround and where it's tracked.
5. **Cleanup:** what the flow leaves behind, and how to undo it.
6. **Source and tests:** where the feature lives and which tests cover it.

`apps/base/tests/test_feature_map.py` fails when a route in `frontend/js/router.ts` appears in no file here, when a file isn't listed below, when a relative link is broken, or when a file names a path that doesn't exist or an e2e test pytest wouldn't find. Name a test by its pytest node ID: `e2e/test_auth.py::TestLogin::test_login_with_valid_credentials`, or the file alone when all of it is relevant. A new page gets a file, or a section in one.

## Before you start

- `just doctor` passes: the stack is this checkout's, every service is up, and `just seed` has run (see [SKILL.md](../SKILL.md)).
- `APP` is set from `scripts/worktree urls`, as in SKILL.md step 1. Mailpit is at the `Mailpit:` URL it prints.
- You know which login to use. Each file names one; the table in SKILL.md step 3 lists them all. To switch, open `$APP/accounts/logout/` first.
- For an invite, run `just seed` first. Seeded invites expire 7 days after the last run, and `just doctor` doesn't check them. Rerunning gives each pending invite its 7 days again.
- No modal or toast is open, and the page has finished loading (wait for its heading).

## Driving conventions

- **Select by role, label, placeholder or visible text**, as `e2e/` does: `get_by_role("button", name="Sign In", exact=True)`, `get_by_label("Email Address")`, `get_by_placeholder("Password")`. Nothing in the SPA has a test id. When a heading and a button share a name ("Sign In"), match the role too.
- **Wait for an end state, never a fixed sleep:** a heading, a toast, a URL, an enabled button, a row in a list.
- **Read the console and the failed network requests on every flow.** A 4xx or 5xx from `/api/` or `/_allauth/` is usually the bug. `docker compose logs web` (or `worker`, for emails and background tasks) has the server side.
- **Emails land in Mailpit**, sent by the `worker` service. If one never arrives, check `worker` is running (`just doctor` says so). Open the newest message and follow its link with the same browser session.
- **`wait_for_function` takes a function, not an expression:** `page.wait_for_function("n => window.items.length === n", arg=3)`. The Content-Security-Policy has no `'unsafe-eval'`, so a bare expression string fails.
- **Labels are Title Case** (see AGENTS.md "UI copy"), so a button is "Send Invite", not "Send invite". Messages, toasts and hints are sentence case, such as "Invitation sent.".
- **Some actions use the browser's `confirm()` or `prompt()`** (removing an email address, regenerating recovery codes, renaming or removing a passkey). Accept them with `page.once("dialog", ...)` before clicking.
- **Keep the browser in the user's timezone.** Give the browser context `timezone_id="America/Chicago"`, the seeded logins' timezone, as `e2e/conftest.py` does. In any other timezone the "Your Timezone Has Changed" modal opens, and its backdrop blocks every click until it's answered ([app-shell.md](app-shell.md)).

## Cleaning up

`just seed` isn't a reset. Each run creates the seeded rows that are missing, gives the seeded logins back their names, passwords and roles, removes their two-factor authentication and passkeys, and gives each pending invite its 7 days again. It leaves alone:

- **Memberships.** It never removes one, and it skips the invite of anyone who has since joined that organization.
- **Whatever a flow created:** organizations, accounts, teams, invites, notifications, email addresses and avatars.
- **Choices users make in the app:** which email address and which organization is primary, and the user's timezone.
- **Settings.** A change to `.env`, such as `ACCOUNT_SIGNUP_OPEN` or the billing keys, stays until you undo it and restart the services that read it.

Each feature file's Cleanup section says what its flow leaves behind. Before changing a choice that seeding keeps, note its value, and set it back afterwards. Use a fresh address or name on the next run rather than one an earlier run used, unless you removed what that run made.

## What stays manual

Skip these steps and say so in your report rather than working around them:

- **Stripe Checkout and the Customer Portal.** Both are full-page redirects to stripe.com and need real test-mode keys. Billing is off unless `BILLING_ENABLED` is on.
- **OS and browser dialogs Playwright can't reach**, such as a native passkey prompt without the virtual authenticator from SKILL.md, or a password manager.
- **Anything that needs a real inbox or phone.** Every email goes to Mailpit; nothing seeded can reach a real address.

## Features

| File | Covers |
|---|---|
| [app-shell.md](app-shell.md) | Home, the header and user menu, theme, timezone prompt, toasts, the 404 page, route guards |
| [sign-in-and-sign-up.md](sign-in-and-sign-up.md) | Signing in (password, passkey, two-factor code), signing up, signing out |
| [password-reset-and-email-verification.md](password-reset-and-email-verification.md) | Resetting a forgotten password, confirming an email address |
| [mfa-and-passkeys.md](mfa-and-passkeys.md) | The Security page: authenticator app, recovery codes, passkeys, reauthentication |
| [account-settings.md](account-settings.md) | Profile, avatar, timezone, email addresses, changing the password |
| [organization-settings.md](organization-settings.md) | An organization's General, Members and Teams tabs |
| [invites.md](invites.md) | Inviting someone to an organization, and accepting or declining an invite |
| [organizations.md](organizations.md) | Switching organizations and creating one |
| [notifications.md](notifications.md) | The bell, the notifications page, and notification preferences |
| [billing.md](billing.md) | The Billing tab and the public pricing page (with `BILLING_ENABLED`) |
| [staff.md](staff.md) | The Django admin, impersonation, test notifications, the Debug Toolbar |
| [cross-cutting-flows.md](cross-cutting-flows.md) | Journeys that span features: an invite end to end, a role change, session expiry |
