# Staff Pages

Tools for staff and superusers: the Django admin, impersonating another user, sending test notifications, and the Debug Toolbar.

## Routes

| Route | Name | |
|---|---|---|
| `/impersonate/` | `impersonate` | `staffOnly` |
| `/test-notifications/` | `test-notifications` | `superuserOnly` |
| `/admin/` | Django admin, server-rendered | `is_staff` |
| `/hijack/acquire/`, `/hijack/release/` | django-hijack, form POSTs | superuser |

The user menu has "Django Admin", and for a superuser who isn't impersonating, "Impersonate User" and "Test Notifications". Outside production a superuser also gets "Mailpit" and "Silo Admin", which open this stack's, on the ports `scripts/worktree urls` prints (`HOST_PORT_MAILPIT` and `HOST_PORT_SILO_CONSOLE`, sent in `/api/app-context/` as `devToolPorts`).

## Login and Data

The superuser: `DJANGO_SUPERUSER_EMAIL` and `DJANGO_SUPERUSER_PASSWORD` in `.env` (Leslie Knope, owner of Pawnee). No other seeded login is staff. The Django admin's "Username" field takes the email address.

## Impersonating a User

1. User menu → "Impersonate User". Type one word (a name, username or email) into the search box. Each field is searched separately, so a full name finds nothing.
2. Wait for the results table, then click a row. The page posts to `/hijack/acquire/` and opens `/` as that user.
3. Expect the banner "Impersonating {name}" (`role="status"`), with "Stop Impersonating" and "Hide Banner".
4. Click "Stop Impersonating" (or the user menu's) to post to `/hijack/release/` and become yourself again.

Only a superuser may impersonate, and never another superuser (`HIJACK_PERMISSION_CHECK`). Starting and stopping select the impersonated user's primary organization, then yours.

## Sending a Test Notification

1. User menu → "Test Notifications". Pick the "Recipient": only staff are listed, so with seeded data only the superuser.
2. Leave "Send Email Notification" and "Send In-App Notification" checked and click "Send".
3. Wait for a toast such as "Email queued and in-app notification sent to {name} ({email})". The email reaches Mailpit through the `worker`.

The in-app notification belongs to the organization you have selected, and sending fails if the recipient isn't a member of it; switch organizations, or to none ([notifications.md](notifications.md)).

## Debug Toolbar

User menu → "Debug Toolbar" (DEBUG only) sets the `debug_toolbar` cookie and reloads. The toolbar shows only when that cookie is `1`, DEBUG is on, and the request comes from an address in `INTERNAL_IPS` (`apps/base/debug_toolbar.py`).

## Known Issues

Tracked in the template's [django-base-site#1424](https://github.com/epicserve/django-base-site/issues/1424), item 3.

- **`/impersonate/` needs only staff, but its search API and hijack need a superuser.** A staff user who isn't a superuser can open the page, but every search fails with 403.

## Cleanup

- **Impersonation:** stop it before switching users or ending the run.
- **Test notifications** stay until deleted ([notifications.md](notifications.md)).
- **The Debug Toolbar** is a cookie, so a new browser context starts with it off.

## Source and Tests

- `frontend/js/views/ImpersonateSearchView.vue`, `frontend/js/views/TestNotificationsView.vue`, `apps/base/debug_toolbar.py`.
- `e2e/test_impersonation.py`: the banner, hiding it, and stopping from it.
- `e2e/test_content_security_policy.py::TestNoPageBreaksThePolicy::test_the_admin`
- `e2e/test_form_labels.py`: the test notification form.
- pytest: `apps/base/tests/test_impersonation_banner.py`, `apps/base/tests/test_test_notifications_api.py`, `apps/base/tests/test_debug_toolbar.py`, `apps/base/tests/test_app_context_api.py` (the Mailpit and Silo ports)
