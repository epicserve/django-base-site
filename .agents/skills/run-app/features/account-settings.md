# Account Settings

A user's own settings: profile photo, name and timezone, email addresses, password, two-factor authentication and notification preferences. Every page has the heading "Account Settings" and the tabs "General", "Email Addresses", "Change Password", "Security" and "Notifications".

## Routes

All `requiresAuth`. User menu → "Account Settings".

| Tab | Route | Name |
|---|---|---|
| General | `/accounts/general/` | `account-general` |
| Email Addresses | `/accounts/email/` | `account-email` |
| Change Password | `/accounts/password/change/` | `account-password-change` |
| Security | `/accounts/security/` | see [mfa-and-passkeys.md](mfa-and-passkeys.md) |
| Notifications | `/accounts/notifications/` | see [notifications.md](notifications.md) |

## Login and Data

Any seeded login. Pick one no other check in progress depends on, since these pages change the account itself.

## Changing the Profile

On General:

1. Change "First Name" and click "Save".
2. Wait for the toast "Your settings were updated.". The home page now greets them by the new name.

**Profile photo:** click "Change Photo" to open "Change Profile Photo". Choose an image with `set_input_files` on its `input[type=file]`, which sits inside the "Choose an Image" label, then click "Save". The photo shows with alt "Profile photo", next to a "Remove" button. Uploads go to Silo.

## Adding an Email Address

On Email Addresses:

1. Under "Add Email Address", fill "Email" with an address no earlier run used, and click "Add".
2. Expect "Email added. Check your inbox for a verification link." and the address listed as "Unverified".
3. The confirmation email goes to Mailpit ([password-reset-and-email-verification.md](password-reset-and-email-verification.md)).

Making an address primary takes selecting its row, then "Make Primary".

## Changing the Password

On Change Password:

1. Fill "Current Password", "New Password" and "New Password (Again)", and click "Change Password".
2. Expect the toast "Your password has been changed." and the fields cleared. The new password signs in; `just seed` puts back `dev-password`.

When the two new passwords differ, "New Password (Again)" shows "The passwords don't match." and nothing is sent: allauth's API takes only the new password, so the page compares them itself.

## Pitfalls

- **Timezone** is a search box whose value is a label such as "Central Time (US & Canada)". Type part of a name, then click the option by its text: the options are list items with no option role.
- **Changing the timezone** away from America/Chicago makes the "Your Timezone Has Changed" modal open in every new browser session set to America/Chicago ([app-shell.md](app-shell.md)), until it's changed back. "Keep Current" silences it only for the rest of that session.
- **Removing an address** asks in a browser `confirm()`; accept it before clicking.
- **Failed sign-ins are rate limited.** A few wrong passwords for one login in a row, as when checking which password now works, get "Too many failed login attempts. Try again later." for a while, even with the right one.

## Cleanup

`just seed` restores the seeded logins' names and passwords. It leaves:

- **The timezone:** set it back to "Central Time (US & Canada)".
- **The photo:** click "Remove".
- **Added addresses:** remove them. Note which address was primary before changing it, and make it primary again; seeding keeps whichever is primary.

## Source and Tests

- Views in `frontend/js/accounts/views/`: `AccountGeneralView.vue`, `AccountEmailView.vue`, `AccountPasswordChangeView.vue`. The tabs: `frontend/js/layouts/AccountLayout.vue`.
- `e2e/test_avatar.py::TestAvatar::test_upload_and_remove`, `e2e/test_avatar.py::TestAvatar::test_choose_an_image_with_the_keyboard`
- `e2e/test_form_labels.py`, `e2e/test_form_errors.py`: the general and add-email forms.
- No e2e test changes the password. Vitest: `frontend/js/accounts/views/AccountPasswordChangeView.test.ts` (the new passwords must match).
- pytest: `apps/accounts/tests/test_api.py`, `apps/accounts/tests/test_avatar_api.py`
