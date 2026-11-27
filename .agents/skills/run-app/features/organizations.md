# Switching and Creating Organizations

A user can belong to several organizations and work in one at a time, or in none ("Personal Space"). They switch between them, mark one as primary (selected each time they sign in), and create new ones.

## Routes

| Route | Name | Meta |
|---|---|---|
| `/organizations/switch/` | `org-switch` | `requiresAuth` |
| `/organizations/create/` | `org-create` | `requiresAuth` |

## Getting There

The header's organization control ([app-shell.md](app-shell.md)):

- **With an organization selected:** its name opens a menu with "Settings", "Switch Company" and "Create Organization".
- **With none selected:** a "Switch Organization" link, or "Create Organization" for someone with no memberships.

The small-screen menu has the same items.

## Login

- `owner@example.com`: in Dunder Mifflin (primary) and Pawnee.
- `user@example.com`: in no organization, so only "Create Organization" shows.

## Switching

`frontend/js/views/OrgSwitchView.vue`, heading "Switch Company":

- **Personal Space:** the first row, a button that clears the selected organization.
- **An organization:** each row is a button named after it, which selects it and goes to `/`.
- **Badges and buttons:** a "Current" badge on the selected one. The primary one has a "Primary" button ("Click to remove primary"), and the others have "Make Primary".
- **Toasts:** "Primary company updated." and "Primary company removed.".

The session keeps the selected organization (`apps/organizations/session.py`). Signing in, and starting or stopping impersonation, selects the user's primary organization, or none (`apps/organizations/signals.py`).

## Creating

`frontend/js/views/OrgCreateView.vue`, heading "Create Organization":

1. Fill "Name". "Account Name" (the slug) fills itself in from it.
2. Click "Create".
3. Wait for the toast "{name} created successfully.". The app opens the new organization's General settings tab.

- **Errors:** a taken slug shows "Account name is already taken.".
- **Ownership:** the creator becomes its owner. It becomes their primary organization only if they had none.

## Endpoints

- `GET /api/organizations/switch-list/`
- `POST /api/organizations/` (create)
- `POST /api/organizations/<slug>/select/`, `POST /api/organizations/<slug>/set-primary/`
- `POST /api/organizations/signout/` (Personal Space)

## Known Issues

- The labels mix "Company" ("Switch Company", "Primary company updated.") and "Organization" ("Switch Organization", "Create Organization").

## Coverage

- `e2e/test_form_errors.py` (creating a blank organization, and one with a taken account name)
- `e2e/test_org_settings.py::TestNonOwner::test_org_menu_hides_settings_link`
- No e2e test drives the switch page.
- pytest: `apps/organizations/tests/test_api.py`
