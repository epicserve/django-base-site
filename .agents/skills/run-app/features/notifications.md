# Notifications

In-app notifications: the bell in the header, the full history at `/notifications/`, and per-category preferences for in-app and email delivery.

## Routes

Both `requiresAuth`:

| Route | Name | |
|---|---|---|
| `/notifications/` | `notifications` | "View All Notifications →" at the bottom of the bell |
| `/accounts/notifications/` | `account-notifications` | An Account Settings tab, and "Preferences →" on the notifications page |

## Login and Data

`just seed` makes no notifications, so make some first:

- As the superuser, send one to yourself from Test Notifications ([staff.md](staff.md)).
- From a shell: `docker compose exec web ./manage.py shell`, then call `notify()` from `apps/notifications/services.py`.

**Notifications belong to an organization.** With an organization selected, the bell and the page show only that organization's; with none selected, only those with no organization. A notification that seems missing usually belongs to another organization, so select the one it was sent in.

## Reading a Notification

1. Open `/notifications/`. An unread row is a button named "Unread, {title}", plus " from {actor}" when someone sent it. The bell reads "Notifications, N unread".
2. Click the row inside `get_by_role("main")`. Without a URL, a dialog named after its title opens; with one, the app goes there.
3. Close the dialog. Expect the row to be named just "{title}" now, and the bell to read one fewer unread.

The bell opens on "Unread" when there are unread ones, and shares the page's select and bulk controls ("Select", "Mark Read", "Mark Unread", "Delete", "Mark All Read").

## Pitfalls

- **The bell and the page have rows with the same names.** On `/notifications/`, scope locators to `get_by_role("main")`.
- **The count updates on a timer.** The bell polls every 20 seconds while the tab is visible, and again when it becomes visible. A notification made from a shell shows up then, as a toast with its title, not at once. Dispatch `visibilitychange` to check sooner.
- **No preferences out of the box.** `NOTIFICATIONS_CATEGORIES` is empty in `config/settings/_base.py`, so the preferences page says "No notification preferences are configured yet.". Once there are some, each checkbox is named by its category and channel, such as "Comments In-App" and "Comments Email".
- **What sends them today:** Test Notifications, the Stripe webhooks, and the trial-ending reminder. Invites and teams send email only.

## Cleanup

Notifications stay until deleted, and seeding doesn't touch them. Delete the ones you made with the bulk "Delete" (on the page, in each organization you sent them in), or from the shell.

## Source and Tests

- `frontend/js/components/AppNotificationBell.vue`, `frontend/js/views/NotificationsView.vue`, `frontend/js/accounts/views/AccountNotificationsView.vue`. `notify()` and email delivery: `apps/notifications/services.py`.
- `e2e/test_notifications.py`: the unread count, the page following the bell, and new notifications arriving.
- `e2e/test_form_labels.py::TestFormLabels::test_every_form`: the preference checkboxes' names.
- pytest: `apps/notifications/tests/`
