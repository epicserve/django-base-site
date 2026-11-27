# Notifications

In-app notifications: the bell in the header, the full history at `/notifications/`, and per-category preferences for in-app and email delivery.

## Routes

| Route | Name | Meta |
|---|---|---|
| `/notifications/` | `notifications` | `requiresAuth` |
| `/accounts/notifications/` | `account-notifications` | `requiresAuth` (an Account Settings tab) |

## Login and Data

`just seed` creates no notifications, so make some first. Either option works with any login, but a notification only shows in the organization it belongs to (see below):

- As the superuser, send one to yourself from Test Notifications ([staff.md](staff.md)).
- From a shell: `docker compose exec web ./manage.py shell`, then call `apps.notifications.services.notify()`.

Notifications are scoped to an organization. With an organization selected, the bell and the page show only that organization's; with none, only those that have no organization. A notification that seems missing usually belongs to another organization.

## Bell

`frontend/js/components/AppNotificationBell.vue`, in every signed-in header:

- **Button:** "Notifications", or "Notifications, N unread".
- **Tabs:** "Unread" opens first when there are unread items, otherwise "All".
- **Header buttons:** "Select", and "Mark All Read" on the Unread tab.
- **Rows:** each is a button named "Unread, {title} from {actor}" ("Unread, " only while unread), with a "Delete Notification" icon button.
- **Opening a row** marks it read. With a URL, the app goes there; otherwise a modal shows the title and body (or "No additional details.") with "Close".
- **Select mode:** "Select All (n)" / "Clear (n)", "Mark Read", "Mark Unread", "Delete", and "Cancel Selection".
- **Empty states:** "You're all caught up." on Unread, "No notifications yet." on All.
- **Footer:** "View All Notifications →".

The bell polls the unread count every 20 seconds while the tab is visible, and again when it becomes visible. A new notification shows as a toast with its title.

## Notifications Page

`frontend/js/views/NotificationsView.vue`:

- **Header:** "Notifications" with the link "Preferences →".
- **Tabs and controls:** "All" and "Unread N", with the same select and bulk controls as the bell.
- **Pagination:** 25 a page, with "Previous Page" and "Next Page".
- **Selecting rows:** scope locators to `get_by_role("main")`, because the bell's rows have the same names.

## Preferences

`frontend/js/accounts/views/AccountNotificationsView.vue`, heading "Notification Preferences":

- **Out of the box:** a new project has no categories (`NOTIFICATIONS_CATEGORIES = []` in `config/settings/_base.py`), so the page says "No notification preferences are configured yet.".
- **With categories:** a table with the headers Category, In-App and Email, and a checkbox for each.

## How They're Made

- **In-app:** `notify()` (`apps/notifications/services.py`) creates the rows. It skips a recipient who turned off in-app delivery for the category.
- **Email:** sent separately with `send_email()`, which queues it for the `worker`, so it lands in Mailpit.
- **What sends them today:** Test Notifications, the Stripe webhooks, and the trial-ending reminder. Invites and teams send email only.
- **Retention:** old notifications are deleted after `NOTIFICATIONS_RETENTION_DAYS` (90) by a beat task.

## Endpoints

`/api/notifications/`:

- `GET /`, `GET /unread-count/`
- `POST /bulk/`
- `GET`, `PATCH` and `DELETE` on `/<id>/`
- `GET /preferences/`, `PATCH /preferences/<category>/`

## Known Gaps

- The preference checkboxes have no labels.

## Coverage

- `e2e/test_notifications.py`:
  - `TestUnreadCount::test_bulk_action_on_unread`, `TestUnreadCount::test_bulk_mark_unread`, `TestUnreadCount::test_delete`, `TestUnreadCount::test_open`
  - `TestPageFollowsBell::test_open`, `TestPageFollowsBell::test_delete`, `TestPageFollowsBell::test_bulk_mark_read`, `TestPageFollowsBell::test_mark_all_read`
  - `TestNewNotifications::test_show_on_the_page`
- pytest: `apps/notifications/tests/`
