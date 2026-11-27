# Staff Pages

Tools for staff and superusers: the Django admin, impersonating another user, sending test notifications, and the Debug Toolbar.

## Routes

| Route | Name | Meta |
|---|---|---|
| `/impersonate/` | `impersonate` | `requiresAuth`, `staffOnly` |
| `/test-notifications/` | `test-notifications` | `requiresAuth`, `superuserOnly` |
| `/admin/` | Django admin (server-rendered, not in the SPA) | `is_staff` |
| `/hijack/acquire/`, `/hijack/release/` | django-hijack (form POSTs) | superuser |

## Login

The superuser: `DJANGO_SUPERUSER_EMAIL` and `DJANGO_SUPERUSER_PASSWORD` in `.env` (Leslie Knope, owner of Pawnee). No other seeded login is staff.

## Django Admin

Open `$APP/admin/`. Its login form's "Username" field takes the email address. The user menu's "Django Admin" and the home page's "Open Django Admin" link there.

## Impersonation

User menu → "Impersonate User" (`frontend/js/views/ImpersonateSearchView.vue`):

1. The page shows "Impersonate User". Type one word (a name, username or email) into the search box (placeholder "Search by name, username, or email..."). Each field is searched separately, so a full name finds nothing.
2. Wait for the results table (Name, Email, Username), then click a row, or use the arrow keys and Enter. The page posts to `/hijack/acquire/` and opens `/` as that user.
3. A banner (`role="status"`) reads "Impersonating {name}", with "Stop Impersonating" ("Stop" on small screens) and "Hide Banner". Hiding lasts until the next impersonation.
4. Stop with the banner's button or the user menu's "Stop Impersonating". Either posts to `/hijack/release/`.

- **No match:** `No users found matching "{query}"`.
- **Who may:** only a superuser may impersonate, and never another superuser (`HIJACK_PERMISSION_CHECK`).
- **Organization:** starting and stopping select the impersonated user's primary organization, then yours.

## Test Notifications

User menu → "Test Notifications" (`frontend/js/views/TestNotificationsView.vue`):

1. Pick the "Recipient" (placeholder "Select a staff user..."). It lists only staff, so with seeded data only the superuser.
2. Leave "Send Email Notification" and "Send In-App Notification" checked, or clear one.
3. Click "Send" and wait for a toast such as "Email queued and in-app notification sent to {name} ({email})".
4. The in-app notification belongs to the organization you have selected. The email goes through the `worker` to Mailpit.

- **Errors:** "Select at least one notification channel.", or that the recipient isn't a member of the selected organization (switch organizations, or to none).

## Debug Toolbar

User menu → "Debug Toolbar" (DEBUG only). It sets the `debug_toolbar` cookie and reloads. The toolbar shows only when the cookie is `1`, DEBUG is on, and the request comes from an address in `INTERNAL_IPS` (`apps/base/debug_toolbar.py`).

## Known Issues

- `/impersonate/` only needs staff, but its search API and hijack need a superuser. A staff user who isn't a superuser can open the page, but every search fails with 403.

## Coverage

- `e2e/test_impersonation.py`:
  - `TestImpersonationBanner::test_banner_shows_who_is_impersonated`
  - `TestImpersonationBanner::test_hide_lasts_until_the_next_impersonation`
  - `TestImpersonationBanner::test_stop_impersonating_from_the_banner`
- `e2e/test_content_security_policy.py::test_the_admin`
- `e2e/test_form_labels.py` (the test notification form)
- pytest: `apps/base/tests/test_impersonation_banner.py`, `apps/base/tests/test_test_notifications_api.py`, `apps/base/tests/test_debug_toolbar.py`
