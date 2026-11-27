---
name: fix-bug
description: Turn a bug report into a verdict with evidence (reproduced, not reproduced, or already fixed on main) by driving the running app, then fix a reproduced bug test-first. Use when given a bug report, a screenshot of something broken, an error message, or "X doesn't work", or when asked to investigate, reproduce, triage, or fix a bug.
---

# Reproduce a bug, then fix it test-first

Reach a verdict before you change any code, and back it with what you saw in the running app, not with what the code suggests. Then fix it under a test that failed first.

## 1. Find the feature

Read the [feature map](../run-app/features/README.md) and pick the feature file the report matches: by the page or route it names, the text in its screenshot, the action it describes, or the email it mentions. A journey that crosses features is in `cross-cutting-flows.md`. From that file, note:

- the route, and the menus that lead there
- the login that shows the feature (and the role or state the report implies: an owner, a member, no organization, an invitee)
- the steps and the text to wait for
- the e2e tests that cover it, and what stays manual

When a report could match more than one feature, say which you picked and why. A "Known Issues" entry that matches is a lead, not a verdict: those were read from the source, so it still needs reproducing.

When the report is too vague to drive (no page, no action, no error), list what you'd need and ask, rather than guess at a flow.

## 2. Reproduce it on current `main`

Reproduce on the latest `main`, so the verdict holds for the code a fix would land on:

```bash
git fetch origin
git merge-base --is-ancestor origin/main HEAD && echo "HEAD has the latest main"
```

If this checkout is a branch made for this bug and it has the latest `main`, use it. Otherwise make one, which is also where the fix will go:

```bash
wt switch --create fix-<short-name> --base origin/main
```

A report about a change in progress on another branch is the exception: reproduce it on that branch, and say so in the verdict.

Then follow the [`run-app` skill](../run-app/SKILL.md): start the stack, `just seed`, `just doctor` until it passes, sign in as the feature file's login. Drive the steps from the report, or the feature file's steps toward the screen it shows. On every attempt, collect:

- **The steps**, as you'd hand them to someone else: the login, each URL, each click and value typed, and what you waited for.
- **A screenshot** of the broken state, or of the correct state when it doesn't reproduce, and the path it was saved to. The Playwright MCP saves under the directory it was started in, which may be the main checkout's `.playwright-mcp/` rather than this worktree.
- **The console errors and the failed requests** (status, method and path, and the response body of an `/api/` or `/_allauth/` error).
- **The server's side**: the matching lines from `docker compose logs --no-color --since 10m web | grep '<the failing path>'`, or `worker` for emails and background tasks. Mailpit for an email that should or shouldn't have arrived.

Try the variations the report leaves open before calling it not reproduced: another role from the login table, a small screen, the state the report implies (an expired invite, two-factor on, no organization).

## 3. Report the verdict

Give exactly one, naming the commit you checked (`git rev-parse --short HEAD`):

| Verdict | It means |
|---|---|
| **Reproduced** | You saw the bug on a checkout that has the latest `origin/main`. When the feature file doesn't say what should happen in that state, say the expected behavior is yours. |
| **Not reproduced** | You followed the steps and their likely variations on the latest `main`, and the app did what the feature file says it should. Say what you tried and what would help: the reporter's steps, their login's role, the version they ran, a screenshot. |
| **Already fixed on `main`** | It doesn't happen on the latest `main`, and you can show it did before: a commit on `main` that changed this behavior (`git log origin/main -- <the files involved>`, or `git log -S '<text from the screenshot>'`), or the bug seen on an older checkout, such as one behind `origin/main`. Name the commit. |

The report:

```
Verdict: reproduced, on <commit>
Feature: <feature file>, login <login>
Steps:
  1. ...
Expected: ...
Actual: ...
Evidence: <screenshot path>, console and network errors, log lines
Cause: <file:line and why>, or "not confirmed yet"
```

Stop after the report when the verdict is **not reproduced** or **already fixed on `main`**: change no code. Do the same when the fix is a product decision rather than a defect (who may sign up, what a role may do, a change to the copy users see): give the options, and ask which one before writing code. When a bug is both (the page shows "HTTP 403" instead of the server's message, and it's an open question whether the action should be allowed at all), report the two parts separately, offer to fix the defect on its own, and ask about the decision.

## 4. Find the cause in the code

Start from the evidence: the failing request's route in `apps/*/api.py`, the view or component named in the console's stack trace, the text on screen (`grep -rn` for it under `frontend/js/`), the traceback in the logs. Read the code before naming a cause, and cite it as `file:line`. A cause you haven't read in the code is a guess, so report it as "not confirmed yet" rather than state it.

Check whether the same mistake appears elsewhere (the same helper, the same pattern in a sibling view), and say so in the report, but fix only this bug in this change.

## 5. Write a test that fails, then fix it

1. **Pick the layer.** Use the cheapest one that can observe the bug, as AGENTS.md's "Choosing a Layer" describes: Vitest for logic in a composable or `utils/` function, a mounted component for what it renders, pytest for anything the server decides (permissions, validation, emails), Playwright only for what needs a real browser. Put it beside the tests that already cover the feature, following AGENTS.md's "Testing" section.
2. **Run it and watch it fail** for the bug's reason: its assertion fails with the wrong value you saw in the app. A test that fails on an import error, a missing fixture or a typo proves nothing, so fix that and run it again.
3. **Fix the code** until the test passes. Keep the change to this bug.
4. **Drive the same steps in the browser again**, and confirm the app now does what the feature file says.
5. **Update the feature file**: remove its "Known Issues" entry if it had one, change any steps or text the fix changed, add the state you found if it had none (and fix a wrong login or step you hit on the way), and add the new test under "Source and Tests", by its pytest node ID (`e2e/test_x.py::TestClass::test_y`), when it's an e2e test.

## 6. Check and hand off

Run `just verify`. When the change touches the SPA or a flow an e2e test covers, also run `just test_e2e`.

One bug per pull request. Its description gives the verdict and the evidence from step 3, the cause with its `file:line`, and names the test that failed before the fix and passes after it.
