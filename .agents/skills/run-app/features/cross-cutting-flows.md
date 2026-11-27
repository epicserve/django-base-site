# Cross-Cutting Flows

Journeys that span features. Each lists its steps, the end state to wait for at each, how to clean up, and the feature files with the detail.

## An Invite, End to End

Covers [invites.md](invites.md), [organization-settings.md](organization-settings.md) and [sign-in-and-sign-up.md](sign-in-and-sign-up.md).

**Before you start:** signup is closed unless `ACCOUNT_SIGNUP_OPEN` is on, and while it's closed, inviting an address that has no account is refused. Set `ACCOUNT_SIGNUP_OPEN=on` in `.env` and run `docker compose restart web`. Pick an address no earlier run used, such as `david.wallace@dundermifflin.example`.

1. **Send the invite.** Sign in as `owner@example.com`. On `/organizations/dunder-mifflin/settings/members/`, click "Invite by Email" and invite the address. Wait for "Invitation sent." and the address under "Pending Invitations".
2. **Find the email.** In Mailpit, open the newest message, "Invite from Michael Scott". If it hasn't arrived, check `worker` is running (`just doctor`) and read `docker compose logs worker`.
3. **Open the link.** Sign out (`$APP/accounts/logout/`), then open the email's "Join Dunder Mifflin Paper Company, Inc." link. Expect "You're Invited!".
4. **Sign up.** Click "Create an Account to Join" and sign up with the invited address. Signup keeps `?next=`, so it comes back to the invite.
5. **Accept.** Click "Accept Invitation" and wait for "You've Joined Dunder Mifflin Paper Company, Inc.!".
6. **Check the result.** Sign back in as the owner. The new member is on the Members tab, and the invite is gone from "Pending Invitations".

**Clean up:**

- Put `ACCOUNT_SIGNUP_OPEN` back as it was and restart `web`.
- The new account and its membership stay. Remove the member on the Members tab, and delete the user in the Django admin as the superuser ([staff.md](staff.md)), or use another address next time.
- If the flow stopped before step 5, cancel the leftover invite under "Pending Invitations".

`e2e/test_invite_flow.py` covers steps 3 to 5 for an existing account, without the email.

## A Role Change Takes Effect at Once

Covers [organization-settings.md](organization-settings.md). The app reads the current role from the database on every load, so a change applies without signing in again.

1. **Before the change.** Sign in as `member@example.com` and open `/organizations/dunder-mifflin/settings/members/`. Expect to land on `/`; the organization menu has no "Settings".
2. **Make the change.** In a second browser context, sign in as `owner@example.com`. On the Members tab, click "Change Role" on Dwight Schrute's row, then "OK" in the dialog. Wait for "Role updated.".
3. **After the change.** Back in the first context, reload. The organization menu now has "Settings", and the Members tab opens.

**Clean up:** `just seed` makes Dwight a member again. Changing him to owner also sent him an email, which stays in Mailpit.

`e2e/test_org_settings.py::TestChangeRole::test_an_owner_makes_a_member_an_owner` covers the owner's side.

## The Session Ends

Covers [sign-in-and-sign-up.md](sign-in-and-sign-up.md) and [app-shell.md](app-shell.md). A 401 from `/api/` while the app thinks someone is signed in sends them to sign in again, then back to the page they were on (`frontend/js/utils/sessionExpiry.ts`).

1. **End the session.** Sign in and open a page, such as `/notifications/`. Delete the session cookie from the browser context. It's named by `SESSION_COOKIE_NAME`: `sessionid` in the main checkout, and its own name in a worktree (see its `.env`).
2. **Trigger an API call** without reloading: use the page (open the bell), or dispatch `visibilitychange`.
3. **Expect** `/accounts/login/?next=/notifications/&session=expired`, with "Your session has ended. Sign in again to pick up where you left off.".
4. **Sign in** and expect to return to `/notifications/`.

A full reload instead lands on the plain login page with no notice, because the app loads signed out. A 401 from `/_allauth/` never counts: allauth sends one on purpose while a two-factor code is pending.

**Clean up:** nothing; only the browser's cookie changed.

`e2e/test_session_expiry.py::TestWhenTheSessionEnds::test_the_next_api_call_sends_you_to_sign_in_and_back` covers this flow.
