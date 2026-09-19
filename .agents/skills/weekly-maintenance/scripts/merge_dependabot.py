#!/usr/bin/env python3
"""
Merge Dependabot PRs one at a time, only while CI is green.

Usage:
    merge_dependabot.py [--repo OWNER/NAME] [--merge-method merge|squash|rebase]
                        [--budget SECONDS] [--poll SECONDS] [--dry-run] PR [PR ...]

For each PR, in ascending number order:
  * refuses to touch PRs not authored by Dependabot
  * waits while checks are pending or GitHub is still computing mergeability
  * when the PR has conflicts or is behind main (normal after a sibling PR that
    touched the same lockfile merged) it comments `@dependabot rebase` once and
    waits for the new head to go green
  * merges only when every check has passed
  * gives up on a PR (and continues with the next) when checks fail, Dependabot
    cannot rebase, or branch protection blocks the merge

Re-running is safe: all state is re-read from GitHub. Exit codes:
  0  every requested PR is merged
  1  finished, but some PRs were held back (see summary)
  2  time budget exhausted; re-run the same command to continue
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta

# Keep the skill directory clean: importing the sibling module must not leave a __pycache__ in the repo.
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dependabot_report import ci_status, load_repo, merge_method, repo_args  # noqa: E402

DEPENDABOT_LOGINS = {"app/dependabot", "dependabot[bot]", "dependabot"}
REBASE_COMMAND = "@dependabot rebase"
REBASE_WINDOW = timedelta(minutes=20)
NO_CHECKS_GRACE = timedelta(minutes=5)
SETTLE_AFTER_MERGE = 10
TRANSIENT_MERGE_ERRORS = (
    "not mergeable",
    "base branch was modified",
    "clean status",
    "cannot be cleanly created",
    "expected head sha",
    "unknown mergeability",
)
PR_FIELDS = "number,title,url,state,author,isDraft,mergeStateStatus,mergeable,headRefOid,statusCheckRollup,comments"


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def gh(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(["gh", *args], capture_output=True, text=True)  # noqa: S603, S607
    if check and result.returncode != 0:
        sys.stderr.write(result.stderr)
        sys.exit(f"`gh {' '.join(args[:2])}` failed with exit code {result.returncode}")
    return result


def fetch_pr(number: int, repo: str | None) -> dict:
    result = gh("pr", "view", str(number), "--json", PR_FIELDS, *repo_args(repo))
    return json.loads(result.stdout)


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def last_rebase_request(pr: dict) -> datetime | None:
    """Return when a human (or this script) last asked Dependabot to rebase."""
    latest = None
    for comment in pr.get("comments") or []:
        login = (comment.get("author") or {}).get("login", "")
        if login in DEPENDABOT_LOGINS:
            continue
        if REBASE_COMMAND in (comment.get("body") or "").lower():
            created = parse_time(comment["createdAt"])
            if latest is None or created > latest:
                latest = created
    return latest


def dependabot_gave_up(pr: dict, since: datetime) -> str | None:
    """First line of a Dependabot reply (after `since`) saying it could not rebase."""
    for comment in pr.get("comments") or []:
        login = (comment.get("author") or {}).get("login", "")
        if login not in DEPENDABOT_LOGINS or parse_time(comment["createdAt"]) < since:
            continue
        body = comment.get("body") or ""
        if any(word in body.lower() for word in ("conflict", "couldn't", "could not", "unable", "can't")):
            return body.strip().splitlines()[0][:160]
    return None


def process(
    number: int, args: argparse.Namespace, method: str, delete_flag: list[str], deadline: float
) -> tuple[str, str]:
    """Drive one PR to a terminal state. Returns (merged|held|timeout, detail)."""
    merge_attempts = 0
    no_checks_since: dict[str, float] = {}
    while True:
        pr = fetch_pr(number, args.repo)
        login = (pr.get("author") or {}).get("login", "")
        head = pr["headRefOid"][:7]
        if login not in DEPENDABOT_LOGINS:
            return "held", f"not a Dependabot PR (author {login}); refusing to merge"
        if pr["state"] == "MERGED":
            return "merged", "already merged"
        if pr["state"] == "CLOSED":
            return "held", "PR is closed"
        if pr.get("isDraft"):
            return "held", "draft PR"

        ci, details = ci_status(pr.get("statusCheckRollup"))
        merge_state = pr.get("mergeStateStatus") or "UNKNOWN"
        needs_rebase = merge_state in ("DIRTY", "BEHIND") or pr.get("mergeable") == "CONFLICTING"

        if needs_rebase:
            requested_at = last_rebase_request(pr)
            now = datetime.now(UTC)
            if requested_at is None or now - requested_at > REBASE_WINDOW:
                if args.dry_run:
                    return "held", f"{merge_state} on {head}; would comment '{REBASE_COMMAND}' and wait"
                gh("pr", "comment", str(number), "--body", REBASE_COMMAND, *repo_args(args.repo))
                log(f"#{number} is {merge_state} on {head}; asked Dependabot to rebase")
            else:
                reason = dependabot_gave_up(pr, requested_at)
                if reason:
                    return "held", f"Dependabot could not rebase: {reason}"
                log(f"#{number} still {merge_state} on {head}; waiting for Dependabot to rebase")
        elif ci == "failing":
            return "held", f"CI failing on {head}: {', '.join(details)}"
        elif ci == "none":
            first_seen = no_checks_since.setdefault(head, time.time())
            if time.time() - first_seen > NO_CHECKS_GRACE.total_seconds():
                return (
                    "held",
                    f"no CI checks reported for {head} after {int(NO_CHECKS_GRACE.total_seconds() // 60)} minutes",
                )
            log(f"#{number} {head}: no checks reported yet; waiting")
        elif ci == "pending" or merge_state == "UNKNOWN":
            what = f"CI pending ({', '.join(details)})" if ci == "pending" else "GitHub computing mergeability"
            log(f"#{number} {head}: {what}; waiting")
        elif merge_state == "BLOCKED":
            return "held", "CI is green but branch protection blocks the merge (required review or check?)"
        else:
            if args.dry_run:
                return "merged", f"DRY RUN: CI green on {head}; would run `gh pr merge {number} --{method}`"
            result = gh("pr", "merge", str(number), f"--{method}", *delete_flag, *repo_args(args.repo), check=False)
            if result.returncode == 0:
                log(f"#{number} merged ({head})")
                return "merged", f"merged {head}"
            error = " ".join(result.stderr.split())
            merge_attempts += 1
            if merge_attempts >= 3 or not any(marker in error.lower() for marker in TRANSIENT_MERGE_ERRORS):
                return "held", f"`gh pr merge` failed: {error[:200]}"
            log(f"#{number} merge attempt {merge_attempts} failed ({error[:120]}); retrying")

        if time.time() + args.poll > deadline:
            return "timeout", f"still waiting on {head} (CI {ci}, merge state {merge_state})"
        time.sleep(args.poll)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("numbers", nargs="+", type=int, metavar="PR", help="PR numbers to merge")
    parser.add_argument("--repo", help="OWNER/NAME; defaults to the repo of the current directory")
    parser.add_argument(
        "--merge-method",
        choices=["merge", "squash", "rebase"],
        help="default: merge commit if the repo allows it, else squash, else rebase",
    )
    parser.add_argument("--budget", type=int, default=480, help="seconds to spend before exiting 2 (default 480)")
    parser.add_argument("--poll", type=int, default=30, help="seconds between GitHub polls (default 30)")
    parser.add_argument("--dry-run", action="store_true", help="report what would happen; never comment or merge")
    args = parser.parse_args()

    info = load_repo(args.repo)
    method = args.merge_method or merge_method(info)
    delete_flag = [] if info.get("deleteBranchOnMerge") else ["--delete-branch"]
    deadline = time.time() + args.budget
    numbers = sorted(set(args.numbers))
    log(
        f"{info['nameWithOwner']}: merging {len(numbers)} PR(s) with --{method}"
        f"{' (dry run)' if args.dry_run else ''}, budget {args.budget}s"
    )

    results: list[tuple[int, str, str]] = []
    timed_out = False
    for index, number in enumerate(numbers):
        if timed_out:
            results.append((number, "not started", "time budget exhausted"))
            continue
        status, detail = process(number, args, method, delete_flag, deadline)
        results.append((number, status, detail))
        if status == "timeout":
            timed_out = True
        elif status == "merged" and not args.dry_run and index < len(numbers) - 1:
            time.sleep(SETTLE_AFTER_MERGE)

    labels = {"merged": "merged", "held": "held back", "timeout": "waiting", "not started": "not started"}
    print("\n## Merge results\n")
    print("| PR | Result | Detail |")
    print("|---|---|---|")
    for number, status, detail in results:
        print(f"| #{number} | {labels.get(status, status)} | {detail} |")

    if timed_out:
        print("\nTime budget exhausted. Re-run the same command to continue; it resumes from GitHub state.")
        return 2
    if any(status != "merged" for _, status, _ in results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
