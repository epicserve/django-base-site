# Sign In and Sign Up

Signing in with a password or a passkey, entering a two-factor code when the account has one, signing up, and signing out. allauth runs headless (`HEADLESS_ONLY`), so every page here is the SPA calling `/_allauth/browser/v1/...`.

## Routes

| Route | Name | |
|---|---|---|
| `/accounts/login/` | `login` | `guest`: a signed-in user is sent home |
| `/accounts/signup/` | `signup` | `guest` |
| `/accounts/2fa/` | `two-factor` | |
| `/accounts/logout/` | `logout` | |

Open `/accounts/logout/` before switching users.

## Login and Data

Any seeded login (SKILL.md step 3). For the two-factor step, set up an authenticator app on `user@example.com` first ([mfa-and-passkeys.md](mfa-and-passkeys.md)). Signing up needs signup open (see Pitfalls).

## Signing In

1. Open `$APP/accounts/login/`, with `?next=<path>` to land on a page afterwards.
2. Fill the fields with the placeholders "Email" and "Password". They have no labels.
3. Click the button named exactly "Sign In": the heading says "Sign In" too.
4. Wait for the URL to leave `/accounts/login/`. Signing in reloads the whole page.

From there:

- **A wrong password** shows "The email address and/or password you specified are not correct." under the password field.
- **`next`** must be a path on this site. Other sites and `/accounts/*` paths fall back to `/` (`frontend/js/utils/redirect.ts`).
- **With two-factor authentication on**, it goes to `/accounts/2fa/?next=...` ("Two-Factor Authentication"). Fill "Code" with the authenticator app's 6-digit code, or a recovery code, and click "Continue". A wrong code shows "Invalid code.". Make a code with `current_totp_code(secret)` from `apps/accounts/tests/totp.py`, which waits out the end of a 30-second window so the code doesn't expire before the server checks it.
- **With an unverified email**, it goes to `/accounts/verification-sent/`.
- **After the session ended**, `?session=expired` adds a notice ([cross-cutting-flows.md](cross-cutting-flows.md)).

## Signing In with a Passkey

The login page offers passkeys two ways: autofill on the email field, which starts when the page loads, and the button "Sign In with a Passkey". Both need the virtual authenticator from SKILL.md and an enrolled passkey ([mfa-and-passkeys.md](mfa-and-passkeys.md)). Once a passwordless passkey is enrolled, autofill signs that user straight in when the login page opens.

## Signing Up and Out

- **Signing up:** fill "Email" and "Password" and click "Sign Up". Email verification is optional, so the new user is signed in and sent to `next` (or `/`), and a confirmation email goes to Mailpit.
- **Signing out:** user menu → "Sign Out", or open `/accounts/logout/`. It shows "Signing out..." and loads `/accounts/login/`.

## Pitfalls

- **Signup is closed** unless `ACCOUNT_SIGNUP_OPEN` is on, and a new project's `.env` leaves it off. The page then shows "Sign up is currently closed.". To sign up, set `ACCOUNT_SIGNUP_OPEN=on` in `.env` and run `docker compose restart web`.
- **Signing out answers 401.** The `DELETE` to `/_allauth/browser/v1/auth/session` returns 401 when it succeeds. That's allauth's design, not an error. So does a pending two-factor sign-in.

## Known Issues

Tracked in the template's [django-base-site#1424](https://github.com/epicserve/django-base-site/issues/1424), item 3.

- **"Create an Account"** shows on the login page even while signup is closed, and leads to "Sign up is currently closed.".

## Cleanup

- **Signup:** put `ACCOUNT_SIGNUP_OPEN` back as it was and restart `web`. The new account stays; delete it in the Django admin as the superuser ([staff.md](staff.md)), or sign up with a fresh address next time.
- **Two-factor authentication** set up for this: `just seed` removes it from the seeded logins.

## Source and Tests

- Views in `frontend/js/accounts/views/`: `LoginView.vue`, `TwoFactorView.vue`, `SignupView.vue`.
- `e2e/test_auth.py`: signing in and out, `next`, redirects, and the passkey prompt (`e2e/test_auth.py::TestPasskeyPrompt`).
- `e2e/test_one_time_codes.py::TestOneTimeCodeFields::test_sign_in`: the two-factor code.
- `e2e/test_passkeys.py::TestSignInWithAPasskey::test_loads_the_app_context_once`
- `e2e/test_form_errors.py` (a wrong password), `e2e/test_session_expiry.py`
- pytest: `apps/accounts/tests/test_auth_flows.py`
- Vitest: `frontend/js/utils/redirect.test.ts`, `frontend/js/utils/routeGuard.test.ts`
