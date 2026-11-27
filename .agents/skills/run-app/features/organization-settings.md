# Organization Settings

An organization's settings, in tabs: General, Members, Teams, and Billing when billing is on ([billing.md](billing.md)). Owners change members' roles, remove members, invite people ([invites.md](invites.md)), and build teams.

## Routes

All under `/organizations/<slug>/settings/` (`requiresAuth`). The bare path redirects to General.

| Tab | Route | Name | Permission |
|---|---|---|---|
| General | `general/` | `org-settings-general` | `manage_settings` |
| Members | `members/` | `org-settings-members` | `manage_members` |
| Teams | `teams/` | `org-settings-teams` | `manage_teams` |
| Billing | `billing/` | `org-settings-billing` | `manage_billing` |

Header → the organization's name → "Settings". The link is hidden from someone who can't open any tab.

## Login and Data

- `owner@example.com` for Dunder Mifflin (`/organizations/dunder-mifflin/settings/`): 20 members, two teams, and three invites, one of them expired. An owner has all four permissions (`apps/organizations/roles.py`).
- `member@example.com` for what someone without the permissions sees: a member has none.

## Changing a Role

As the owner, on the Members tab (a table with the headers Name, Email and Role):

1. Click "Change Role" on Dwight Schrute's row. The dialog asks "Change Dwight Schrute's role from member to owner?".
2. Click "OK" and wait for the toast "Role updated.". His badge reads "Owner", and he gets an email.

Removing a member works the same way: the icon button titled "Remove", then "OK", then "Member removed.". The removed member gets an email.

## Adding a Team

As the owner, on the Teams tab:

1. Click "Add Team". In the modal, fill "Name" and pick people from "Members" (a combobox, placeholder "Add members...").
2. Click "Save" and wait for "Team created.". The team appears in the table with its members.

## Pitfalls

- **A tab the user can't open** sends them to the first tab they can, or home if there's none, so a plain member who opens any settings URL lands on `/`.
- **The session decides the organization.** Every tab acts on the organization selected in the session, not the slug in the URL. Switch organizations first ([organizations.md](organizations.md)).
- **The server refuses** removing yourself, and removing or demoting the last owner; that error names the permission nobody else would hold. Your own row's buttons are disabled.
- **Teams' row buttons** ("Edit" and "Delete") stay transparent until hover, but Playwright can still click them.
- **With billing on**, a plan without teams shows "Teams Aren't Included on Your Current Plan" in place of the Teams tab's content.
- **General** is a placeholder with no form.

## Cleanup

- **Roles and removed seeded members:** `just seed` restores the seeded roles and adds back seeded members who were removed.
- **Teams:** `just seed` recreates a deleted seeded team and adds back its seeded members, but never removes a team or a member. Delete a team you added. A renamed seeded team stays, and seeding makes another with the original name, so rename it back instead.
- **Emails** from role changes and removals stay in Mailpit.

## Source and Tests

- Tabs and their permissions: `frontend/js/utils/orgSettings.ts`, inside `frontend/js/layouts/OrgSettingsLayout.vue`. Members: `frontend/js/apps/ManageOrganizationApp.vue`. Teams: `frontend/js/apps/ManageTeamsApp.vue`. General: `frontend/js/views/settings/GeneralView.vue`.
- `e2e/test_org_settings.py`: listing every page of members, the invite list, changing a role, and what a member sees.
- `e2e/test_form_errors.py`, `e2e/test_form_labels.py`: the team and invite forms.
- pytest: `apps/organizations/tests/`, `apps/teams/tests/`
- Vitest: `frontend/js/utils/orgSettings.test.ts`, `frontend/js/utils/routeGuard.test.ts`
