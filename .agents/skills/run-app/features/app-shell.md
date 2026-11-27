# App Shell

What surrounds every signed-in page: the home page, the header with its organization menu and user menu, the theme toggle, the timezone prompt, toasts, and the 404 page. Also the route guards that decide where a page sends someone who can't open it.

## Routes

| Route | Name | Meta |
|---|---|---|
| `/` | `home` | `requiresAuth` |
| any unknown path | `not-found` | none |

`App.vue` wraps a page in `AppLayout` only when someone is signed in and the route doesn't set `publicChrome`, so a signed-out 404 has no header. The app shows "Loading..." until `/api/app-context/` answers.

## Login

Any seeded login. `owner@example.com` has an organization; `user@example.com` has none, so the header shows "Create Organization". The staff-only menu items need the superuser.

## What's on Screen

- **Home** (`frontend/js/views/HomeView.vue`): heading "Hi {first name}, let's build something." ("Hi there" without a first name), the link "Read the Docs", "Open Django Admin" for staff, and the section "What's in the Box".
- **Header** (`frontend/js/layouts/AppLayout.vue`), left to right:
  - The site name, linking to `/`.
  - The bell (see [notifications.md](notifications.md)).
  - The organization control. With an organization selected, a button named after it opens "Settings" (only when the user can open a settings tab), "Switch Company" and "Create Organization". With none selected, a "Switch Organization" link, or "Create Organization" for someone with no memberships. See [organizations.md](organizations.md).
  - The user menu, opened by the avatar button. Its items:
    - "Account Settings", the theme row ("Theme"), "Sign Out".
    - "Django Admin" for staff.
    - "Impersonate User" and "Test Notifications" for a superuser who isn't impersonating; "Stop Impersonating" while impersonating. See [staff.md](staff.md).
    - "Mailpit" and "Silo Admin" for a superuser outside production.
    - "Debug Toolbar" with "On" or "Off", only with DEBUG on.
- **Small screens:** below Tailwind's `lg` breakpoint a menu button ("Open Menu" / "Close Menu") replaces the header controls and repeats the same items, plus the user's name and email.
- **Theme** (`ThemeToggle.vue`): buttons "Light Theme", "Dark Theme" and "Auto Theme" with `aria-pressed`. The choice goes in `localStorage.theme` and `<html data-theme>`.
- **Timezone prompt** (`TimezoneDetectModal.vue`): when the browser's timezone differs from the user's, the modal "Your Timezone Has Changed" offers "Keep Current" and "Update Timezone". Its backdrop blocks every click until answered. It doesn't appear on guest pages, on the two-factor and reauthentication pages, or while impersonating. Set the browser context's `timezone_id` to the user's timezone (the default is in `apps/accounts/models.py`) to keep it away, as `e2e/conftest.py` does.
- **Toasts** (`AppToast.vue`): bottom right, in the region "Notifications (F8)", for 4 seconds (5 for a new notification).
- **New version:** after a deploy, "A new version of the app is available." with a "Reload" button.
- **404** (`NotFoundView.vue`): heading "404", "Page Not Found", link "Go Home".

## Route Guards

`frontend/js/utils/routeGuard.ts`, unit-tested in `routeGuard.test.ts`:

| Route meta | Who | Goes to |
|---|---|---|
| `requiresAuth` | signed out | `/accounts/login/?next=<path>` |
| `guest` | signed in | `/` |
| `staffOnly` | not staff | `/` |
| `superuserOnly` | not a superuser | `/` |
| an org settings tab | lacks its permission | the first tab they can open, else `/` |
| `pricing` | billing off | `/` signed in, else the login page |

A page that "just goes home" is usually one of these.

## Known Gaps

- The avatar button that opens the user menu has no accessible name. Click it by position (after the bell and the organization control), or open "Account Settings" at `/accounts/general/` directly.
- Toast close buttons have no label.
- The "Mailpit" and "Silo Admin" links use the default ports (8025, 9001), so in a worktree they open the main checkout's. Use the URLs from `scripts/worktree urls`.

## Coverage

- `e2e/test_auth.py::test_logout_cancels_the_timezone_check`
- `e2e/test_scroll.py`, `e2e/test_styles.py`, `e2e/test_content_security_policy.py`
- Vitest: `frontend/js/utils/routeGuard.test.ts`
