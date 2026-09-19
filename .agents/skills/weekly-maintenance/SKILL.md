---
name: weekly-maintenance
description: Weekly dependency maintenance for the GitHub repo in the current directory. Reviews every open Dependabot PR, shows which packages jump more than a patch release (grouped per PR), and when CI is green asks whether to merge them all, then merges them one at a time. Use when asked to do weekly maintenance, review or merge Dependabot PRs, or catch up on dependency updates.
argument-hint: "[--dry-run] [--yes] [--repo OWNER/NAME]"
model: sonnet
effort: low
allowed-tools:
  - Bash(${CLAUDE_SKILL_DIR}/scripts/dependabot_report.py)
  - Bash(${CLAUDE_SKILL_DIR}/scripts/dependabot_report.py *)
  - Bash(${CLAUDE_SKILL_DIR}/scripts/merge_dependabot.py *)
  - Bash(gh pr view *)
  - Bash(gh pr checks *)
  - Bash(gh run view *)
  - AskUserQuestion
---

# Weekly maintenance: review and merge Dependabot PRs

Arguments: `$ARGUMENTS`

- `--dry-run`: show the report and stop. Never merge.
- `--yes`: skip the confirmation question and merge every ready PR (for unattended runs).
- `--repo OWNER/NAME`: act on that repo instead of the one in the current directory. Pass it through to both scripts.

Both scripts need an authenticated `gh` CLI and Python 3. They are the only way this skill merges anything. Never run `gh pr merge` yourself.

## 1. Gather the report

```bash
${CLAUDE_SKILL_DIR}/scripts/dependabot_report.py
```

## 2. Show the report

Relay the report's Markdown to the user as is: the summary table, the per-PR tables of upgrades larger than a patch release, any notes, and the merge readiness list. Do not collapse the per-PR package tables into a sentence. The point of this step is that the user sees every major and minor bump, grouped by PR, before deciding.

## 3. Decide

- No open PRs: say so and stop.
- `--dry-run`: stop after the report.
- Nothing ready (every PR held back): explain why each one is held back (CI failing, CI pending, conflicts, draft) and stop. Suggest re-running once CI finishes or the failure is fixed.
- Otherwise ask with AskUserQuestion, unless `--yes` was passed. One single-select question, options in this order:
  1. `Merge all N ready PRs`. Add "(Recommended)" when every open PR is ready.
  2. `Merge only the patch-level PRs`. Offer this only when at least one ready PR is patch-only and at least one is not.
  3. `Don't merge anything`.

  Say that specific PR numbers can be typed instead. If some PRs are held back, say the options cover only the ready ones and repeat which are held back.

## 4. Merge

Run the merge script with the chosen PR numbers and a 10 minute Bash timeout (600000 ms):

```bash
${CLAUDE_SKILL_DIR}/scripts/merge_dependabot.py 1338 1339 1340
```

Exit codes:

- `0`: everything merged.
- `1`: finished, but some PRs were held back. The summary table says why.
- `2`: time budget exhausted while waiting on CI or a Dependabot rebase. Run the exact same command again; it resumes from GitHub state. Keep going until it exits 0 or 1. If the same PR is still "waiting" after three runs, stop and report it as stuck.

Why it takes a while: sibling PRs that touch the same lockfile (uv.lock, bun.lock) conflict as soon as the first one merges. The script comments `@dependabot rebase`, waits for the new commit's CI to go green, then merges. Expect about 5 minutes per rebased PR.

## 5. Report

Finish with a short summary: which PRs merged, which were held back and why, and the next step if there is one (fix a failing check, re-run the skill later).

## Notes

- Only Dependabot PRs are ever merged. The merge script refuses other authors.
- The merge method defaults to a merge commit when the repo allows it, then squash, then rebase. Override with `--merge-method squash` on the merge script.
- "More than a patch release" means the major or minor number changed. Minor bumps on 0.x versions are flagged because they may be breaking. Versions that do not look like semver (commit SHAs, dates) show as `unknown` and are treated as above patch so they get looked at.
