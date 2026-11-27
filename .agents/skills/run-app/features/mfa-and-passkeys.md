# Two-Factor Authentication and Passkeys

The Security tab of Account Settings: an authenticator app (TOTP), recovery codes, and passkeys, which can sign someone in without a password or act as a second factor. Changes here may first ask for the password again.

## Routes

All `requiresAuth`. User menu → "Account Settings" → "Security".

| Route | Name |
|---|---|
| `/accounts/security/` | `account-security` |
| `/accounts/security/totp/` | `account-totp` |
| `/accounts/security/recovery-codes/` | `account-recovery-codes` |
| `/accounts/security/passkeys/` | `account-passkeys` |
| `/accounts/reauthenticate/` | `account-reauthenticate` |

The Security page has three sections, each with its button: "Authenticator App (TOTP)" ("Set Up" or "Manage"), "Recovery Codes" ("View" once codes exist), and "Passkeys" ("Add" or "Manage").

## Login and Data

`user@example.com`, so the logins with organizations stay free of two-factor authentication. Sign in shortly before making a change, or allauth asks for the password again first (see Pitfalls).

## Setting Up an Authenticator App

1. On the Security page, click "Set Up". The page shows a QR code (alt "TOTP QR code", served by `/qr/`) and "Or enter this key manually:" followed by the secret.
2. Read the secret from the page and make a code with `current_totp_code(secret)` (`apps/accounts/tests/totp.py`). It waits out the end of a 30-second window, so the code doesn't expire before the server checks it.
3. Fill "6-Digit Code", click "Enable", and wait for "Authenticator app enabled.". Ten recovery codes are made at the same time.

From then on, signing in asks for a code ([sign-in-and-sign-up.md](sign-in-and-sign-up.md)). "Disable Authenticator App" turns it off, after a browser `confirm()`.

## Adding a Passkey

1. Give the tab a virtual authenticator over CDP before opening any page (SKILL.md, "Testing passkeys").
2. On `/accounts/security/passkeys/`, under "Add a Passkey", fill "Name". Leave "Allow this passkey to sign me in without a password" checked for a passwordless passkey, or clear it for a second factor.
3. Click "Add Passkey" and wait for "Passkey added.". The row shows "Passwordless" or "Two-Factor".

With a passwordless passkey enrolled, the virtual authenticator answers the login page's autofill request by itself, so opening `/accounts/login/` signs that user straight in.

## Pitfalls

- **Reauthentication.** Once the last sign-in is old enough, allauth asks for the password again. On the authenticator app page, that's an overlay "Confirm Your Password" (not a dialog role) with "Password" and "Continue". For recovery codes and passkeys, it's a redirect to `/accounts/reauthenticate/?next=...`; fill "Password", click "Continue", and expect to come back. e2e tests skip this by signing in with the `sign_in` fixture, which records a fresh password sign-in.
- **Browser dialogs.** Disabling the app and regenerating recovery codes use `confirm()`; renaming a passkey uses `prompt()` and removing one `confirm()`. Answer each with `page.once("dialog", lambda d: d.accept())` (or `d.accept("New name")`) before clicking.
- **Passkeys need `localhost`.** `SITE_DOMAIN` has to be on `localhost`, never `127.0.0.1`, which WebAuthn rejects. A browser without WebAuthn shows "This browser doesn't support passkeys.".
- **The virtual authenticator lasts for the life of the tab.** A new tab or context has none, and can't use a passkey enrolled through another.

## Cleanup

`just seed` removes every authenticator (the app, recovery codes and passkeys) from the seeded logins, so the password alone signs them in again.

## Source and Tests

- Views in `frontend/js/accounts/views/`: `AccountSecurityView.vue`, `AccountTotpView.vue`, `AccountRecoveryCodesView.vue`, `AccountPasskeysView.vue`, `ReauthenticateView.vue`. allauth serves them under `/_allauth/browser/v1/account/authenticators/`.
- `e2e/test_one_time_codes.py::TestOneTimeCodeFields::test_authenticator_app_setup`
- `e2e/test_passkeys.py::TestAddPasskey::test_add`: passwordless and two-factor.
- `e2e/test_content_security_policy.py`: the security, authenticator app and passkeys pages.
- pytest: `apps/accounts/tests/test_mfa_flows.py`
