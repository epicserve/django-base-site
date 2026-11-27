# Organization Settings

An organization's settings, in tabs: General, Members, Teams, and Billing when billing is on ([billing.md](billing.md)). Owners manage members' roles and remove them, invite people ([invites.md](invites.md)), and build teams.

## Routes

All under `/organizations/<slug>/settings/` (`requiresAuth`), in `frontend/js/layouts/OrgSettingsLayout.vue`. The bare path redirects to General.

| Tab | Route | Name | Permission |
|---|---|---|---|
| General | `general/` | `org-settings-general` | `manage_settings` |
| Members | `members/` | `org-settings-members` | `manage_members` |
| Teams | `teams/` | `org-settings-teams` | `manage_teams` |
| Billing | `billing/` | `org-settings-billing` | `manage_billing` |

The tabs and their permissions are in `frontend/js/utils/orgSettings.ts`; roles grant permissions in `apps/organizations/roles.py`. An owner has all four; a member has none.

A tab the user can't open sends them to the first one they can, or home if there's none, so a plain member who opens any settings URL lands on `/`. Every tab acts on the organization selected in the session, not the slug in the URL.

## Getting There

Header → the organization's name → "Settings". The link is hidden from someone who can't open any tab.

## Login

- `owner@example.com` for Dunder Mifflin (`/organizations/dunder-mifflin/settings/`), with 20 members, two teams and three invites, one of them expired.
- `member@example.com` for what someone without the permissions sees.

## General

`frontend/js/views/settings/GeneralView.vue` is a placeholder: "General Organization Settings" with a note to add fields. It has no form.

## Members

`frontend/js/apps/ManageOrganizationApp.vue`.

- **Member list:** a table with the headers Name, Email and Role. Role badges read "Owner" and "Member". The list loads every page of members.
- **Changing a role:** "Change Role" on a row swaps member and owner. It asks "Change {name}'s role from member to owner?" with "Cancel" and "OK", then the toast "Role updated.". Changing someone to owner emails them.
- **Removing a member:** the icon button titled "Remove" asks "Remove {name} from {organization}?", then the toast "Member removed.". The removed member gets an email.
- **Your own row:** both buttons are disabled.
- **Server-side refusals:** removing yourself, and removing or demoting the last owner ("Give someone else the owner role first.").
- **Invites:** "Invite a Member" and "Pending Invitations" are on this tab; see [invites.md](invites.md).

## Teams

`frontend/js/apps/ManageTeamsApp.vue`, inside `<FeatureGate feature="teams">`.

- **List:** "Add Team" opens the modal. The table has the headers Name and Members. An empty list reads "No teams found.", and a team with no members shows "No members".
- **Row buttons:** icon buttons titled "Edit" and "Delete". They stay transparent until hover, but Playwright can still click them.
- **Modal:** "Add Team" or "Edit Team", with the fields "Name" and "Members" (a combobox, placeholder "Add members..."), and the buttons "Cancel" and "Save" ("Update" when editing). Saving with a blank name shows "Name is required.".
- **Toasts:** "Team created.", "Team updated.", "Team deleted.".
- **Deleting:** asks `Are you sure you want to delete "{name}"?`.
- **Plan gate:** with billing on and a plan without teams, the tab shows "Teams Aren't Included on Your Current Plan" instead.

## Endpoints

- `/api/organization-members/` (`manage_members`)
- `/api/teams/` (`manage_teams`)
- `/api/organization-invites/` (`manage_members`)

## Coverage

- `e2e/test_org_settings.py`:
  - `TestMembersTab::test_lists_every_page` and `TestMembersTab::test_invites`
  - `TestChangeRole::test_an_owner_makes_a_member_an_owner`
  - `TestNonOwner::test_org_menu_hides_settings_link` and `TestNonOwner::test_settings_redirect_home`
- `e2e/test_form_errors.py`, `e2e/test_form_labels.py` (the team and invite forms)
- pytest: `apps/organizations/tests/` (`test_api.py`, `test_last_owner.py`, `test_roles.py`, `test_member_privacy.py`), `apps/teams/tests/`
- Vitest: `frontend/js/utils/orgSettings.test.ts`, `frontend/js/utils/routeGuard.test.ts`
