# App Shell

What surrounds every signed-in page: the home page, the header with its organization menu and user menu, the theme toggle, the timezone prompt, toasts, and the 404 page. Also the route guards that decide where a page sends someone who can't open it.

## Routes

| Route | Name | |
|---|---|---|
| `/` | `home` | `requiresAuth` |
| any unknown path | `not-found` | Signed out, it has no header |

The app shows "Loading..." until `/api/app-context/` answers.

## Login and Data

Any seeded login. `owner@example.com` has an organization; `user@example.com` has none, so the header shows "Create Organization". The staff-only menu items need the superuser ([staff.md](staff.md)).

## What's on Screen

- **Home:** the heading "Hi {first name}, let's build something.", and "Open Django Admin" for staff.
- **Header**, left to right: the site name (a link to `/`), the bell ([notifications.md](notifications.md)), the organization control ([organizations.md](organizations.md)), and the avatar button, "User Menu", that opens the user menu.
- **User menu:** "Account Settings", the theme buttons ("Light Theme", "Dark Theme", "Auto Theme", with `aria-pressed`) and "Sign Out" for everyone. Staff and superusers get more ([staff.md](staff.md)), and "Debug Toolbar" shows only with DEBUG on.
- **Small screens:** below Tailwind's `lg` breakpoint, a menu button ("Open Menu" / "Close Menu") replaces the header controls and repeats their items.
- **Toasts:** bottom right, in the region "Notifications (F8)", for 4 seconds (5 for a new notification).
- **404:** the heading "404", "Page Not Found", and "Go Home".

## Route Guards

`frontend/js/utils/routeGuard.ts`. A page that "just goes home" is usually one of these:

| Route meta | Who | Goes to |
|---|---|---|
| `requiresAuth` | signed out | `/accounts/login/?next=<path>` |
| `guest` | signed in | `/` |
| `staffOnly` | not staff | `/` |
| `superuserOnly` | not a superuser | `/` |
| an org settings tab | lacks its permission | the first tab they can open, else `/` |
| `pricing` | billing off | `/` signed in, else the login page |

## Pitfalls

- **The timezone prompt** ("Your Timezone Has Changed", with "Keep Current" and "Update Timezone") opens when the browser's timezone differs from the user's, and its backdrop blocks every click until it's answered. Give the browser context the user's timezone (`timezone_id="America/Chicago"` for a seeded login), as `e2e/conftest.py` does. It doesn't open on guest pages, on the two-factor and reauthentication pages, or while impersonating.

## Cleanup

The theme is kept in the browser's `localStorage`, so a new browser context starts fresh. Answering the timezone prompt with "Update Timezone" changes the user's timezone; see [account-settings.md](account-settings.md) to set it back.

## Source and Tests

- `frontend/js/App.vue` (which layout wraps a page), `frontend/js/layouts/AppLayout.vue` (the header and menus), `frontend/js/views/HomeView.vue`.
- `e2e/test_auth.py::TestLogout::test_logout_cancels_the_timezone_check`
- `e2e/test_avatar.py::TestAvatar::test_upload_and_remove`: the "User Menu" button, with initials and with a photo
- `e2e/test_scroll.py`, `e2e/test_styles.py`, `e2e/test_content_security_policy.py`
- Vitest: `frontend/js/utils/routeGuard.test.ts`
