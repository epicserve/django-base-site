# Password Reset and Email Verification

Resetting a forgotten password through an emailed link, and confirming an email address through an emailed link. Both emails come from the `worker`, so they land in Mailpit.

## Routes

| Route | Name |
|---|---|
| `/accounts/password/reset/` | `password-reset` |
| `/accounts/password/reset/done/` | `password-reset-done` |
| `/accounts/password/reset/key/<key>/` | `password-reset-key` |
| `/accounts/password/reset/key/done/` | `password-reset-key-done` |
| `/accounts/confirm-email/<key>/` | `confirm-email` |
| `/accounts/verification-sent/` | `verification-sent` |

The four reset pages are `guest`, so sign out first. The links in the emails have no trailing slash (`HEADLESS_FRONTEND_URLS` in `config/settings/_base.py`).

## Login and Data

- **Resetting:** any seeded email.
- **Verifying:** every seeded address is already verified, so add a new address to a seeded login ([account-settings.md](account-settings.md)), or sign up with signup open.

## Resetting a Password

1. Open `/accounts/password/reset/`, fill the placeholder "Email", and click "Reset My Password". Wait for "Check Your Email".
2. In Mailpit, open "Password Reset Email" and follow its link to `/accounts/password/reset/key/<key>`.
3. On "Set New Password", fill "New Password" and click "Reset Password". Wait for "Password Changed".

A used or bad link shows "Invalid Reset Link". An unregistered email still gets "Check Your Email", and Mailpit gets an "Unknown Account" email instead.

## Confirming an Email Address

1. Adding an address on the Email Addresses page, or signing up, sends "Please Confirm Your Email Address".
2. Follow its link to `/accounts/confirm-email/<key>`. Wait for "Email Confirmed".
3. Expect the address to show "Verified" on `/accounts/email/`.

A used or expired link shows "Link No Longer Valid". A reload after a success still shows success.

## Pitfalls

- **A successful reset answers 401.** `POST /_allauth/browser/v1/auth/password/reset` returns 401 with `is_authenticated: false` when it works. That's allauth's design, not an error.
- **Sign-in goes to "Verify Your Email"** (`/accounts/verification-sent/`) when it needs a verified address first.

## Cleanup

- **A reset password:** `just seed` puts the seeded logins' passwords back to `dev-password`.
- **An added address:** remove it on `/accounts/email/` ([account-settings.md](account-settings.md)).

## Source and Tests

- Views in `frontend/js/accounts/views/`: the `PasswordReset*View.vue` files, `EmailConfirmView.vue`, `VerificationSentView.vue`.
- No e2e test drives either flow. `e2e/test_content_security_policy.py` loads the reset page.
- pytest: `apps/accounts/tests/test_auth_flows.py`, `apps/accounts/tests/test_email_verification_flow.py`
