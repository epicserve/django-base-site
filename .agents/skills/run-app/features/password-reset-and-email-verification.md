# Password Reset and Email Verification

Resetting a forgotten password through an emailed link, and confirming an email address through an emailed link. Both emails come from the `worker`, so they land in Mailpit.

## Routes

| Route | Name | Meta |
|---|---|---|
| `/accounts/password/reset/` | `password-reset` | `guest` |
| `/accounts/password/reset/done/` | `password-reset-done` | `guest` |
| `/accounts/password/reset/key/<key>/` | `password-reset-key` | `guest` |
| `/accounts/password/reset/key/done/` | `password-reset-key-done` | `guest` |
| `/accounts/confirm-email/<key>/` | `confirm-email` | none |
| `/accounts/verification-sent/` | `verification-sent` | none |

The reset pages are guest-only, so sign out first. The email links have no trailing slash (`HEADLESS_FRONTEND_URLS` in `config/settings/_base.py`).

## Login

- **Resetting:** any seeded email. Rerun `just seed` afterwards to put the password back to `dev-password`.
- **Verification:** add a new address to a seeded login ([account-settings.md](account-settings.md)), or sign up with signup open. Every seeded address is already verified.

## Resetting a Password

1. **Request the link.** Open `/accounts/password/reset/` ("Password Reset"). Fill the placeholder "Email" and click "Reset My Password".
2. **Wait** for "Check Your Email".
3. **Find the email.** In Mailpit, open "Password Reset Email" and follow its link to `/accounts/password/reset/key/<key>`.
4. **Set the password.** On "Set New Password", fill "New Password", click "Reset Password", and wait for "Password Changed". A "Sign In" link follows.

- **Bad or used link:** shows "Invalid Reset Link" with "Request New Reset Link".
- **Unregistered email:** the request still says "Check Your Email". Mailpit gets an "Unknown Account" email with a signup link instead.

## Confirming an Email Address

1. **Get the email.** Signing up, or adding an address on the Email Addresses page, sends "Please Confirm Your Email Address".
2. **Follow its link** to `/accounts/confirm-email/<key>`. The page shows "Confirming Email", then "Email Confirmed".
3. **Expect** the address to show "Verified" on `/accounts/email/`.

- **Used or expired link:** "Link No Longer Valid". Signed in, it adds "This link has already been used. Your email is confirmed.". A reload after a success still shows success.
- **"Verify Your Email"** (`/accounts/verification-sent/`) is where sign-in goes when it needs a verified address first.

## Endpoints

- `POST /_allauth/browser/v1/auth/password/request`
- `POST /_allauth/browser/v1/auth/password/reset` (answers 401 with `is_authenticated: false` when it succeeds)
- `POST /_allauth/browser/v1/auth/email/verify`

## Coverage

- No e2e test drives either flow. `e2e/test_content_security_policy.py` loads the reset page.
- pytest: `apps/accounts/tests/test_auth_flows.py`, `apps/accounts/tests/test_email_verification_flow.py`
