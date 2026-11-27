# Account Settings

A user's own settings: profile photo, name and timezone, email addresses, password, two-factor authentication and notification preferences. Every page has the heading "Account Settings" and the tabs "General", "Email Addresses", "Change Password", "Security" and "Notifications" (`frontend/js/layouts/AccountLayout.vue`).

## Routes

All `requiresAuth`:

| Tab | Route | Name |
|---|---|---|
| General | `/accounts/general/` | `account-general` |
| Email Addresses | `/accounts/email/` | `account-email` |
| Change Password | `/accounts/password/change/` | `account-password-change` |
| Security | `/accounts/security/` | see [mfa-and-passkeys.md](mfa-and-passkeys.md) |
| Notifications | `/accounts/notifications/` | see [notifications.md](notifications.md) |

## Getting There

User menu → "Account Settings".

## Login

Any seeded login. Rerun `just seed` to restore the seeded names and password afterwards.

## General

`frontend/js/accounts/views/AccountGeneralView.vue`:

- **Profile photo:**
  1. Click "Change Photo". The dialog "Change Profile Photo" opens.
  2. Choose an image with `set_input_files` on its `input[type=file]`, which sits inside the "Choose an Image" label.
  3. Crop, then click "Save".
  - The photo shows with alt "Profile photo", and a "Remove" button appears.
  - Errors: "Please select a JPEG, PNG, or WebP image.", "Image must be under 10 MB.", "Upload failed. Please try again.".
  - Uploads go to Silo.
- **Name:** "First Name" and "Last Name".
- **Timezone:** "Timezone" is a search box whose value is a label such as "Central Time (US & Canada)". Type part of a name, then click the option by its text: the options are list items with no option role.
- **Saving:** "Save", then the toast "Your settings were updated.".

## Email Addresses

`frontend/js/accounts/views/AccountEmailView.vue`:

- **The list:** each address shows "Primary", "Verified" or "Unverified".
- **Making one primary:** select a row, then click "Make Primary" ("Primary email updated.").
- **Resending the link:** "Resend Verification" ("Verification email sent.", or a request to wait if one was sent recently).
- **Removing one:** "Remove" asks in a browser confirm dialog, then shows "Email removed.".
- **Adding one:** under "Add Email Address", fill "Email" and click "Add". Expect "Email added. Check your inbox for a verification link." and a confirmation email in Mailpit ([password-reset-and-email-verification.md](password-reset-and-email-verification.md)). An address already on the account shows "This email address is already associated with this account.".

## Change Password

`frontend/js/accounts/views/AccountPasswordChangeView.vue`:

1. Fill "Current Password", "New Password" and "New Password (Again)".
2. Click "Change Password".
3. Wait for "Your password has been changed.".

## Endpoints

- `PATCH /api/users/<id>/` (name, timezone)
- `POST` and `DELETE` `/api/avatar/`
- `/_allauth/browser/v1/account/email`
- `POST /_allauth/browser/v1/account/password/change`

## Known Issues

- "New Password (Again)" is never sent or compared, so a mismatch still changes the password to the first field's value.

## Coverage

- `e2e/test_avatar.py::test_upload_and_remove` and `e2e/test_avatar.py::test_choose_an_image_with_the_keyboard`
- `e2e/test_form_labels.py`, `e2e/test_form_errors.py` (the general and add-email forms)
- `e2e/test_scroll.py`
- No e2e test changes the password.
- pytest: `apps/accounts/tests/test_api.py`, `apps/accounts/tests/test_avatar_api.py`
