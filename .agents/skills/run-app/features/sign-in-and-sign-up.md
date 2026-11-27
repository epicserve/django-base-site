# Sign In and Sign Up

Signing in with a password or a passkey, entering a two-factor code when the account has one, signing up, and signing out. allauth runs headless (`HEADLESS_ONLY`), so every page here is the SPA calling `/_allauth/browser/v1/...`.

## Routes

| Route | Name | Meta |
|---|---|---|
| `/accounts/login/` | `login` | `guest` |
| `/accounts/signup/` | `signup` | `guest` |
| `/accounts/2fa/` | `two-factor` | none |
| `/accounts/logout/` | `logout` | none |

A `guest` page sends a signed-in user home, so open `/accounts/logout/` before switching users.

## Login

Any seeded login (SKILL.md step 3). For the two-factor step, set up an authenticator app on `user@example.com` first ([mfa-and-passkeys.md](mfa-and-passkeys.md)); `just seed` removes it again.

## Signing In

`frontend/js/accounts/views/LoginView.vue`, heading "Sign In":

1. Open `$APP/accounts/login/`. Add `?next=<path>` to land on a page after signing in.
2. Fill the placeholders "Email" and "Password". The inputs have no labels.
3. Click the button "Sign In" (role and exact name, since the heading matches too). While busy it reads "Signing In...".
4. Wait for the URL to leave `/accounts/login/`. Signing in reloads the whole page.

- **Wrong password:** "The email address and/or password you specified are not correct." under the password field.
- **Where it lands:** `next` must be a path on this site. Other sites and `/accounts/*` paths fall back to `/` (`frontend/js/utils/redirect.ts`).
- **Two-factor pending:** it goes to `/accounts/2fa/?next=...`. **Email not yet verified:** it goes to `/accounts/verification-sent/`.
- **Session expired:** `?session=expired` adds "Your session has ended. Sign in again to pick up where you left off." (see [cross-cutting-flows.md](cross-cutting-flows.md)).
- **Other links:** "Forgot Password?" ([password-reset-and-email-verification.md](password-reset-and-email-verification.md)) and "Create an Account".

## Signing In with a Passkey

The page offers passkeys two ways: autofill on the email field, which starts when the page loads, and the button "Sign In with a Passkey" ("Waiting for Passkey…" while busy). Both need the virtual authenticator from SKILL.md and an enrolled passkey ([mfa-and-passkeys.md](mfa-and-passkeys.md)). Once a passwordless passkey is enrolled, autofill signs that user straight in when the login page opens.

## Two-Factor Code

`frontend/js/accounts/views/TwoFactorView.vue`:

1. The page shows "Two-Factor Authentication". Fill "Code" with the 6-digit code from the authenticator app, or a recovery code.
2. Click "Continue" ("Verifying…" while busy). A wrong code shows "Invalid code.".
3. The page then goes to `next`. If the pending sign-in expired (410), it goes back to the login page.

Make a code with `current_totp_code(secret)` from `apps/accounts/tests/totp.py`. It waits out the last seconds of the 30-second window, so the code doesn't expire before the server checks it.

## Signing Up

`frontend/js/accounts/views/SignupView.vue`:

- **Signup closed:** signup is off unless `ACCOUNT_SIGNUP_OPEN` is on, and a new project's `.env` leaves it off. The page then shows "Sign up is currently closed.". To try signing up, set `ACCOUNT_SIGNUP_OPEN=on` in `.env` and restart `web`.
- **Signup open:** heading "Sign Up". Fill "Email" and "Password", then click "Sign Up" ("Creating Account..." while busy).
- **After signing up:** email verification is optional, so the new user is signed in and sent to `next` (or `/`). A confirmation email still goes to Mailpit.

## Signing Out

User menu → "Sign Out", or open `/accounts/logout/`. The page shows "Signing out...", ends the session, and loads `/accounts/login/`.

The `DELETE` to `/_allauth/browser/v1/auth/session` answers 401 when it succeeds. That's allauth's design, not an error.

## Known Issues

- "Create an Account" shows on the login page even while signup is closed.

## Coverage

- `e2e/test_auth.py`:
  - `TestLogin::test_login_with_valid_credentials`, `TestLogin::test_next_cannot_leave_the_site`
  - `TestLogout::test_logout_redirects_to_login`
  - `TestAuthRedirects::test_unauthenticated_user_redirected_to_login`
  - `TestSignInLoadsTheAppContextOnce`, `TestPasskeyPrompt`
- `e2e/test_one_time_codes.py::test_sign_in`
- `e2e/test_passkeys.py::TestSignInWithAPasskey::test_loads_the_app_context_once`
- `e2e/test_form_errors.py` (a wrong password), `e2e/test_session_expiry.py`
- pytest: `apps/accounts/tests/test_auth_flows.py`
- Vitest: `frontend/js/utils/redirect.test.ts`, `frontend/js/utils/routeGuard.test.ts`
