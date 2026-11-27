# Invites

An owner invites someone to an organization by email. The invitee follows the email's link, signs in or signs up, and accepts or declines. An invite lasts 7 days.

## Routes

| Route | Name | Meta |
|---|---|---|
| `/organizations/invite/<key>/accept/` | `accept-invite` | none (works signed out) |
| `/organizations/<slug>/settings/members/` | `org-settings-members` | `requiresAuth`, `manage_members` |

## Login

- **Sending:** `owner@example.com`.
- **Accepting:** `user@example.com`, who has a pending invite to Dunder Mifflin.
- **A wrong user:** `member@example.com` on that same invite.
- **Already a member:** `owner@example.com` on it.
- **Expired:** the `todd.packer@dundermifflin.example` invite.

`just seed` prints every seeded invite's accept URL, since seeded invites send no email.

## Sending an Invite

On the Members tab ([organization-settings.md](organization-settings.md)):

1. Under "Invite a Member", click "Invite by Email".
2. In the modal, fill "Email Address" and click "Send Invite". A blank email shows "Email is required."; the server's field errors show under the field.
3. Wait for the toast "Invitation sent.". The invite appears under "Pending Invitations" (headers Name, Email, Status; status "Pending" or "Expired"), which is hidden while there are none.
4. **The email** is sent by the `worker` once the request commits, so it lands in Mailpit. Its subject is "Invite from {sender's full name}", and its "Join {organization}" button links to `/organizations/invite/<key>/accept/`.

- **Role:** the form has no role field, so an invite from the UI always makes a member. The API takes `role`.
- **Cancelling:** "Cancel" on a pending invite asks "Cancel this invitation?", shows "Invitation cancelled.", and emails the invitee "Your invitation to {organization} has been canceled".
- **Throttle:** 30 invites an hour and 100 a day per user.

## Accepting or Declining

`frontend/js/views/AcceptInviteView.vue` loads the invite from `GET /api/invite-by-key/<key>/`.

| State | Heading and text | Actions |
|---|---|---|
| Loading | "Loading invitation..." | |
| Unknown key | "Invitation Unavailable", "This invitation link is invalid." | |
| Signed out | "You're Invited!", "{sender} invited you to join {organization}." | "Create an Account to Join" (signup with `?next=`), "I Already Have an Account" (login with `?next=`) |
| Signed in | "You're Invited!" | "Accept Invitation", "Decline" |
| Accepted | "You've Joined {organization}!" | "Continue" |
| Declined | "Invitation Declined", "You can close this page." | |
| Expired | "Invitation Expired", "Ask {sender} to send you a new invitation." | |
| Already a member | "Already a Member" | "Continue" |

Accepting (`POST /api/invite-by-key/<key>/accept/`) deletes the invite, adds the membership and selects that organization. Declining (`.../decline/`) deletes the invite. Accepting a seeded invite sticks, since `just seed` never removes memberships; SKILL.md says how to reset `user@example.com`.

## Known Issues

- **Signup is closed by default** (`ACCOUNT_SIGNUP_OPEN` off), so someone invited without an account follows "Create an Account to Join" to "Sign up is currently closed." and can't join.
- **A different signed-in user** sees "You're Invited!" with the buttons, because the lookup doesn't check the email. Accepting or declining then returns 403. The page shows "Invitation Unavailable" with the text "HTTP 403", not the server's message, because `ApiError.message` is the status (`frontend/js/utils/api.ts`).

## Coverage

- `e2e/test_invite_flow.py`:
  - `TestInviteFlow::test_the_invite_page` (signed out, unknown key, expired)
  - `TestInviteFlow::test_existing_user_can_accept`
  - `TestInviteFlow::test_decline_consumes_invite`
  - `TestInviteFlow::test_unauthenticated_accept_redirects_to_login`
- `e2e/test_org_settings.py::TestMembersTab::test_invites`
- pytest: `apps/organizations/tests/test_api.py`, `apps/organizations/tests/test_invite_throttle.py`
- The whole journey, email included: [cross-cutting-flows.md](cross-cutting-flows.md).
