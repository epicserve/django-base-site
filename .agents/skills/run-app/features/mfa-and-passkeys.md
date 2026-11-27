# Two-Factor Authentication and Passkeys

The Security tab of Account Settings: an authenticator app (TOTP), recovery codes, and passkeys, which can sign someone in without a password or act as a second factor. Changes here may first ask for the password again.

## Routes

All `requiresAuth`:

| Route | Name |
|---|---|
| `/accounts/security/` | `account-security` |
| `/accounts/security/totp/` | `account-totp` |
| `/accounts/security/recovery-codes/` | `account-recovery-codes` |
| `/accounts/security/passkeys/` | `account-passkeys` |
| `/accounts/reauthenticate/` | `account-reauthenticate` |

## Getting There

User menu → "Account Settings" → "Security".

## Login

`user@example.com`, so the logins with organizations stay free of two-factor authentication. Rerunning `just seed` removes every authenticator from the seeded logins.

## Security Overview

`frontend/js/accounts/views/AccountSecurityView.vue` has three sections:

- **"Authenticator App (TOTP)":** "Set Up" or "Manage".
- **"Recovery Codes":** "X of Y unused.", with "View" once codes exist.
- **"Passkeys":** "Add" or "Manage", with "N passkey(s) registered.".

## Authenticator App

`frontend/js/accounts/views/AccountTotpView.vue`:

1. Open "Set Up". The page shows a QR code (alt "TOTP QR code", served by `/qr/`) and "Or enter this key manually:" followed by the secret.
2. Read the secret from the page and make a code with `current_totp_code(secret)` (`apps/accounts/tests/totp.py`).
3. Fill "6-Digit Code", click "Enable", and wait for "Authenticator app enabled.". Recovery codes are made at the same time.
4. To turn it off, click "Disable Authenticator App" and accept the browser's confirm dialog. Wait for "Authenticator app disabled.".

Once it's on, signing in asks for a code ([sign-in-and-sign-up.md](sign-in-and-sign-up.md)).

## Recovery Codes

`frontend/js/accounts/views/AccountRecoveryCodesView.vue`, heading "Recovery Codes":

- Lists ten codes.
- "Copy All" shows the toast "Copied to clipboard.".
- "Regenerate" asks in a browser confirm dialog, then shows "New recovery codes generated.".

## Passkeys

`frontend/js/accounts/views/AccountPasskeysView.vue`, heading "Passkeys":

1. Give the tab a virtual authenticator over CDP before opening any page (SKILL.md, "Testing passkeys").
2. Under "Add a Passkey", fill "Name". Leave "Allow this passkey to sign me in without a password" checked for a passwordless passkey, or clear it for a second factor.
3. Click "Add Passkey" ("Adding…" while busy) and wait for "Passkey added.". The row shows "Passwordless" or "Two-Factor".
4. "Rename" opens a browser prompt ("Passkey renamed."). "Remove" opens a browser confirm ("Passkey removed.").

- **Unsupported browser:** "This browser doesn't support passkeys.".
- **Domain:** passkeys need `SITE_DOMAIN` on `localhost`, never `127.0.0.1`.

## Reauthentication

allauth asks for the password again before these changes once the last sign-in is old enough:

- **On the authenticator app page:** an overlay (not a dialog role) "Confirm Your Password", with "Password", "Cancel" and "Continue".
- **For recovery codes and passkeys:** a redirect to `/accounts/reauthenticate/?next=...`. Fill "Password", click "Continue", and expect to return.

Tests skip this step by signing in with `sign_in`, which records a fresh password sign-in. In the browser, sign in shortly before making the change.

## Browser Dialogs

Disabling the app, regenerating codes, renaming a passkey and removing one use `confirm()` or `prompt()`. In Playwright, answer each with `page.once("dialog", lambda d: d.accept())` (or `d.accept("New name")`) before clicking.

## Endpoints

`/_allauth/browser/v1/account/`:

- `authenticators`
- `authenticators/totp`
- `authenticators/recovery-codes`
- `authenticators/webauthn`

Also `/_allauth/browser/v1/auth/reauthenticate`.

## Coverage

- `e2e/test_one_time_codes.py::test_authenticator_app_setup`
- `e2e/test_passkeys.py::TestAddPasskey::test_add` (passwordless and two-factor)
- `e2e/test_content_security_policy.py` (the security, authenticator app and passkeys pages)
- pytest: `apps/accounts/tests/test_mfa_flows.py`
