# Invites

An owner invites someone to an organization by email. The invitee follows the email's link, signs in or signs up, and accepts or declines. An invite lasts 7 days.

## Routes

| Route | Name | |
|---|---|---|
| `/organizations/invite/<key>/accept/` | `accept-invite` | Works signed out |
| `/organizations/<slug>/settings/members/` | `org-settings-members` | Where an owner sends and cancels invites ([organization-settings.md](organization-settings.md)) |

## Login and Data

Run `just seed` first: seeded invites expire 7 days after the last run, and it prints each invite's accept URL, since seeded invites send no email. Every seeded login's password is `dev-password`.

- **Sending:** `owner@example.com`.
- **Accepting:** `user@example.com`, who is in no organization and has a pending invite to Dunder Mifflin.
- **Signed in as someone else:** `ron.swanson@pawnee.example` on that invite. He's only in Pawnee. Don't use `member@example.com`: he's in Dunder Mifflin, so he gets "Already a Member".
- **Already a member:** `owner@example.com` on that invite.
- **Expired:** the `todd.packer@dundermifflin.example` invite.
- **No account:** the `holly.flax@dundermifflin.example` invite. `just seed` makes it with a recipe, not the API, so it exists even though the page would now refuse it while signup is closed (see Sending an Invite). Signed out, "Create an Account to Join" leads to "Sign up is currently closed.", so Holly can't join until signup is open ([sign-in-and-sign-up.md](sign-in-and-sign-up.md)).

## Accepting an Invite

As `user@example.com`:

1. Sign in with `?next=` set to the invite's accept path, or sign in and then open its URL.
2. Expect "You're Invited!" with "Accept Invitation" and "Decline".
3. Click "Accept Invitation" and wait for "You've Joined Dunder Mifflin Paper Company, Inc.!".

Accepting adds the membership, selects the organization and deletes the invite. "Decline" deletes the invite and shows "Invitation Declined".

The page (`frontend/js/views/AcceptInviteView.vue`) shows the first of these that applies:

| Who opens it | Heading | Actions |
|---|---|---|
| Anyone, with an unknown key | "Invitation Unavailable" | |
| Anyone, once the invite has expired | "Invitation Expired" | |
| A member of the organization | "Already a Member" | "Continue" |
| Someone signed out | "You're Invited!" | "Create an Account to Join", "I Already Have an Account" (both keep `?next=`) |
| Anyone else signed in, the invitee or not | "You're Invited!" | "Accept Invitation", "Decline" |

Someone signed in under another address who isn't a member, such as Ron, still gets "Accept Invitation" and "Decline": the lookup doesn't compare emails. Either button returns 403, and the page shows "Invitation Unavailable" with the server's reason, "This invitation was sent to a different email address." A member who isn't the invitee would get the same 403 from the API, but the page shows them "Already a Member" instead of the buttons.

## Sending an Invite

As the owner, on Dunder Mifflin's Members tab:

1. Click "Invite by Email", fill "Email Address" with the address of an account that isn't in Dunder Mifflin and has no invite, such as `ron.swanson@pawnee.example`, and click "Send Invite".
2. Wait for the toast "Invitation sent.". The address appears under "Pending Invitations".
3. The `worker` sends the email to Mailpit, "Invite from Michael Scott". Its "Join Dunder Mifflin Paper Company, Inc." link opens the accept page.

While signup is closed (`ACCOUNT_SIGNUP_OPEN` off, the default), an address that no account has as its email is refused: the modal stays open with "Sign-up is closed, so only someone with an account can accept an invite. Turn on sign-up (ACCOUNT_SIGNUP_OPEN) to invite someone who doesn't have an account." under "Email Address", and nothing is sent. An account matches by its email in any case, the same way accepting does; another address on the account doesn't count. To invite a new address, open signup ([sign-in-and-sign-up.md](sign-in-and-sign-up.md)).

The form has no role field, so an invite sent from the page always makes a member. Sending is throttled to 30 invites an hour and 100 a day per user.

## Pitfalls

- **Never invite a seeded invitee's address from the page.** A second invite to `user@example.com` makes `just seed` fail with `MultipleObjectsReturned`. Cancel the extra invite to fix it. Tracked in [django-base-site#1424](https://github.com/epicserve/django-base-site/issues/1424), item 3.

## Cleanup

- **Accepted as `user@example.com`:** sign in as the owner, remove Ryan Howard on the Members tab, then run `just seed` to recreate the invite. Seeding skips an invite whose invitee has joined.
- **Declined:** `just seed` recreates it.
- **A recreated invite has a new key,** so use the accept URL `just seed` prints after it, not the old one.
- **Sent from the page:** "Cancel" on its row under "Pending Invitations", then "OK". The invitee's cancellation email goes to Mailpit. Seeding never removes an invite.
- **Ron's attempts** change nothing: the 403 comes before anything is deleted, so the same accept URL works again.

## Source and Tests

- The page: `frontend/js/views/AcceptInviteView.vue`. The public lookup, accept and decline: `apps/organizations/api.py`. Sending and cancelling: `frontend/js/apps/ManageOrganizationApp.vue`.
- `e2e/test_invite_flow.py`: signed out, an unknown key, an expired invite, accepting, declining, and "I Already Have an Account" keeping `?next=`.
- `e2e/test_org_settings.py::TestMembersTab::test_invites`: the "Pending Invitations" list. No e2e test sends or cancels an invite; `e2e/test_form_errors.py` checks the invite form's errors.
- Vitest: `frontend/js/views/AcceptInviteView.test.ts`, the server's reason (or a fallback) when accepting or declining fails.
- pytest: `apps/organizations/tests/test_api.py` (`TestCreateInviteWhileSignupIsClosed`: refusing an address without an account while signup is closed), `apps/organizations/tests/test_invite_throttle.py`
- The whole journey, email included: [cross-cutting-flows.md](cross-cutting-flows.md).
