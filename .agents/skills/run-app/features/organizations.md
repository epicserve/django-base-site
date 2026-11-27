# Switching and Creating Organizations

A user can belong to several organizations and work in one at a time, or in none ("Personal Space"). They switch between them, mark one as primary (selected each time they sign in), and create new ones.

## Routes

Both `requiresAuth`:

| Route | Name |
|---|---|
| `/organizations/switch/` | `org-switch` |
| `/organizations/create/` | `org-create` |

The header's organization control ([app-shell.md](app-shell.md)) leads to both. With an organization selected, its name opens a menu with "Switch Company" and "Create Organization". With none selected, it's a "Switch Organization" link, or "Create Organization" for someone in no organization. The small-screen menu has the same items.

## Login and Data

- `owner@example.com`: in Dunder Mifflin (primary) and Pawnee.
- `user@example.com`: in no organization, so only "Create Organization" shows.

## Switching

As the owner, open "Switch Company" (`frontend/js/views/OrgSwitchView.vue`):

1. Each organization is a button named after it, with "Current" on the selected one. "Personal Space", the first row, clears the selection.
2. Click "Pawnee Parks and Recreation". The app selects it and goes to `/`, and the header shows its name.

"Make Primary" on a row makes it the one selected at sign-in ("Primary company updated."). The primary one shows a "Primary" button instead, which removes it. Every other row has its own "Make Primary", and the rows aren't list items, so find the organization's button first and take the "Make Primary" in the same parent element.

## Creating

As `user@example.com`, open "Create Organization" (`frontend/js/views/OrgCreateView.vue`):

1. Fill "Name" with a name no earlier run used. "Account Name" (the slug) fills itself in from it.
2. Click "Create" and wait for the toast "{name} created successfully.". The app opens the new organization's General settings tab.

The creator becomes its owner. It becomes their primary organization only if they had none. A taken slug shows "Account name is already taken.".

## Pitfalls

- **Signing in, and starting or stopping impersonation, select the user's primary organization**, or none (`apps/organizations/signals.py`). The selection lives in the session (`apps/organizations/session.py`).

## Known Issues

Tracked in the template's [django-base-site#1424](https://github.com/epicserve/django-base-site/issues/1424), item 3.

- **The labels mix "Company" and "Organization"** ("Switch Company" in the menu and on the page, "Switch Organization" as the link), so match the exact text.

## Cleanup

- **Primary:** seeding never changes it. Note which organization was primary before, and set it back with "Make Primary".
- **A created organization** stays, with its creator as owner, and seeding never deletes it. Delete it in the Django admin as the superuser ([staff.md](staff.md)). For `user@example.com`, it also ends the no-organization state, and becomes their primary.

## Source and Tests

- The views above, and `apps/organizations/api.py` for switching, selecting, setting the primary and creating.
- `e2e/test_form_errors.py`: creating a blank organization, and one with a taken account name.
- `e2e/test_org_settings.py::TestNonOwner::test_org_menu_hides_settings_link`: the organization menu.
- No e2e test drives the switch page.
- pytest: `apps/organizations/tests/test_api.py`
