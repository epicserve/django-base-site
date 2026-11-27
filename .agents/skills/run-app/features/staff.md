# Staff Pages

Tools for staff and superusers: the Django admin, impersonating another user, sending test notifications, and the Debug Toolbar.

## Routes

| Route | Name | |
|---|---|---|
| `/impersonate/` | `impersonate` | `superuserOnly` |
| `/test-notifications/` | `test-notifications` | `superuserOnly` |
| `/admin/` | Django admin, server-rendered | `is_staff` |
| `/hijack/acquire/`, `/hijack/release/` | django-hijack, form POSTs | superuser |

The user menu has "Django Admin", and for a superuser who isn't impersonating, "Impersonate User" and "Test Notifications". Outside production a superuser also gets "Mailpit" and "Silo Admin", which open this stack's, on the ports `scripts/worktree urls` prints (`HOST_PORT_MAILPIT` and `HOST_PORT_SILO_CONSOLE`, sent in `/api/app-context/` as `devToolPorts`).

## Login and Data

The superuser: `DJANGO_SUPERUSER_EMAIL` and `DJANGO_SUPERUSER_PASSWORD` in `.env` (Leslie Knope, owner of Pawnee). No other seeded login is staff. For a staff user who isn't a superuser, make one in `docker compose exec web python manage.py shell`: `make_user("staff@example.com", password="dev-password", is_staff=True, update=True)` from `apps.accounts.recipes`. It has no organization unless you add one with `make_member`. The Django admin's "Username" field takes the email address.

## Impersonating a User

1. User menu → "Impersonate User". Type one word (a name, username or email) into the search box. Each field is searched separately, so a full name finds nothing.
2. Wait for the results table, then click a row. The page posts to `/hijack/acquire/` and opens `/` as that user.
3. Expect the banner "Impersonating {name}" (`role="status"`), with "Stop Impersonating" and "Hide Banner".
4. Click "Stop Impersonating" (or the user menu's) to post to `/hijack/release/` and become yourself again.

Only a superuser may impersonate, and never another superuser (`HIJACK_PERMISSION_CHECK`). The page, its menu link and its search API (`/api/users/impersonate-search/`) follow the same rule: a staff user who isn't a superuser is sent home from `/impersonate/`. Starting and stopping select the impersonated user's primary organization, then yours.

## Sending a Test Notification

1. User menu → "Test Notifications". Pick the "Recipient": only staff are listed, so with seeded data only the superuser.
2. Leave "Send Email Notification" and "Send In-App Notification" checked and click "Send".
3. Wait for a toast such as "Email queued and in-app notification sent to {name} ({email})". The email reaches Mailpit through the `worker`.

The in-app notification belongs to the organization you have selected, and sending fails if the recipient isn't a member of it; switch organizations, or to none ([notifications.md](notifications.md)).

## Debug Toolbar

User menu → "Debug Toolbar" (DEBUG only) sets the `debug_toolbar` cookie and reloads. The toolbar shows only when that cookie is `1`, DEBUG is on, and the request comes from an address in `INTERNAL_IPS` (`apps/base/debug_toolbar.py`).

## Cleanup

- **Impersonation:** stop it before switching users or ending the run.
- **Test notifications** stay until deleted ([notifications.md](notifications.md)).
- **The Debug Toolbar** is a cookie, so a new browser context starts with it off.

## Source and Tests

- `frontend/js/views/ImpersonateSearchView.vue`, `frontend/js/views/TestNotificationsView.vue`, `apps/base/debug_toolbar.py`.
- `e2e/test_impersonation.py`: the banner, hiding it, and stopping from it.
- `e2e/test_content_security_policy.py::TestNoPageBreaksThePolicy::test_the_admin`
- `e2e/test_form_labels.py`: the test notification form.
- `e2e/test_dev_tool_links.py::TestDevToolLinks::test_links_use_this_stacks_ports`: the "Mailpit" and "Silo Admin" links.
- Vitest: `frontend/js/utils/routeGuard.test.ts` (who may open `/impersonate/`).
- pytest: `apps/base/tests/test_impersonation_banner.py`, `apps/base/tests/test_test_notifications_api.py`, `apps/base/tests/test_debug_toolbar.py`, `apps/base/tests/test_app_context_api.py` (the Mailpit and Silo ports)
