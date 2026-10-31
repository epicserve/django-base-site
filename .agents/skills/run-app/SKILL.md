---
name: run-app
description: Start this project's Docker stack, seed known dev logins with `just seed`, and sign in through a browser (Playwright) to check a UI change. Use when asked to run, start, or screenshot the app, or to check a UI change in the browser.
---

# Run the app and check a UI change

## 1. Start the stack

```bash
docker compose up --wait -d
```

`just start` runs the same stack in the foreground and blocks, so use the detached form. `web` has no healthcheck and runs `migrate` on startup, so wait until the API answers:

```bash
for i in $(seq 1 60); do curl -fs -o /dev/null http://localhost:8000/api/app-context/ && break; sleep 2; done
```

If it never answers, read `docker compose logs web`.

- Always use `http://localhost:8000`, never `127.0.0.1`: passkeys reject bare IPs as the Relying Party ID.
- In development the page loads its JS and CSS from the Vite dev server in the `frontend` service (port 3000). A blank page usually means that service is down: `docker compose logs frontend`.
- Vite hot-reloads frontend changes and `runserver` reloads Python changes, so there's no need to restart after an edit.

## 2. Seed known logins

```bash
just seed
```

It prints the logins and each seeded invite's accept URL. It's safe to rerun: it restores the seeded rows, resets the seeded passwords, and removes any MFA (TOTP, passkeys) from the seeded logins so the password alone signs in. Apart from that it never deletes anything created by hand. It refuses unless `DEBUG` is on in `.env`, and while migrations are still running (wait for step 1, then retry).

## 3. Pick a login

The cast comes from The Office (Dunder Mifflin) and Parks and Recreation (Pawnee). Every seeded login uses the password `dev-password`.

| Login | Who | Use it to check |
|---|---|---|
| `owner@example.com` | Michael Scott: owner of Dunder Mifflin (primary org); member of Pawnee | Org settings (General, Members, Teams), invites, the org switcher |
| `member@example.com` | Dwight Schrute: member of Dunder Mifflin, not an owner | What non-owners see (org settings send them home) |
| `user@example.com` | Ryan Howard: no organization; pending invite to Dunder Mifflin | The no-org state and accepting an invite |
| `admin@example.com` | Leslie Knope: superuser and staff; owner of Pawnee | `/admin/` (sign in with the email), `/impersonate/`, `/test-notifications/` |

The rest of the seeded data:

- Dunder Mifflin (`dunder-mifflin`) has 20 members, for checking long lists and member search. The other 18 are logins such as `jim.halpert@dundermifflin.example`, with the same password. Pawnee Parks and Recreation (`pawnee-parks`) has the Parks crew, such as `ron.swanson@pawnee.example`.
- Teams: Sales and Party Planning Committee at Dunder Mifflin, Harvest Festival at Pawnee.
- Invites to Dunder Mifflin: `user@example.com` (pending), `holly.flax@dundermifflin.example` (pending, no account), `todd.packer@dundermifflin.example` (expired). `just seed` prints their accept URLs because seeded invites send no email.

## 4. Sign in

Use the browser tool you have (the Playwright MCP, or a Playwright script):

1. Open `http://localhost:8000/accounts/login/`. Add `?next=<path>` to land on the page under test, e.g. `?next=/organizations/dunder-mifflin/settings/members/`.
2. Fill the fields with the placeholders `Email` and `Password`.
3. Click the button named exactly `Sign In`. The heading says "Sign In" too, so match the button by role and exact name.
4. Wait for the URL to leave `/accounts/login/`.

To switch users, open `/accounts/logout/` first: a signed-in user who opens the login page is sent home.

Accepting a seeded invite (or making other changes) sticks, because `just seed` never removes memberships. To put `user@example.com` back in the no-org state, sign in as the owner, remove them from Dunder Mifflin in the Members tab, and run `just seed` again to recreate the invite.

### Testing passkeys

The login page offers passkeys through the email field's autofill. To enroll and use one in Chromium, give the tab a virtual authenticator over CDP before opening any page. The Playwright MCP's run-code tool can run this:

```js
async (page) => {
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('WebAuthn.enable');
  await cdp.send('WebAuthn.addVirtualAuthenticator', {
    options: { protocol: 'ctap2', transport: 'internal', hasResidentKey: true, hasUserVerification: true, isUserVerified: true },
  });
}
```

It lasts for the life of the tab. Enroll under `/accounts/security/passkeys/`. Once a passwordless passkey is enrolled, the virtual authenticator answers the login page's autofill request by itself, so opening `/accounts/login/` signs that user straight in. Run `just seed` afterwards to remove the passkey (and the MFA it turned on) from the seeded login.

## 5. Check the change

- Open the changed route, take a screenshot, and read the console for errors and the network log for failed requests. The SPA's routes are in `frontend/js/router.js`.
- Common pages: `/`, `/organizations/<slug>/settings/{general,members,teams}/`, `/accounts/general/`, `/accounts/security/`, `/notifications/`.
- Emails (invites sent from the app, password reset, email verification) land in Mailpit at `http://localhost:8025`.

## 6. Keep it

If the flow is worth guarding, add a Playwright test under `e2e/`. The `_login` fixture in `e2e/test_auth.py` shows the same sign-in steps. Run the suite with `just test_e2e`.
