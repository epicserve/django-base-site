#!/usr/bin/env python3
"""
Report on open Dependabot PRs: CI status, mergeability and per-package bump size.

Usage:
    dependabot_report.py [--repo OWNER/NAME] [--json PATH]

Prints a Markdown report to stdout. With --json PATH the same data is also
written as JSON. Needs an authenticated `gh`; Python standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

GREEN_CONCLUSIONS = {"SUCCESS", "NEUTRAL", "SKIPPED"}
BUMP_ORDER = {"major": 0, "minor": 1, "unknown": 2, "other": 3, "patch": 4}

# Grouped PRs carry one "Updates `pkg` from X to Y" line per package.
UPDATES_RE = re.compile(r"^Updates [`'\"]?([^`'\"\s]+)[`'\"]? from (\S+?) to (\S+?)\.?\s*$", re.M)
# Single-package PRs: "Bumps [pkg](url) from X to Y." or "Bumps pkg from X to Y."
BUMPS_RE = re.compile(
    r"^Bumps (?:\[([^\]]+)\]\([^)]*\)|[`'\"]?([^`'\"\s\[]+)[`'\"]?) from (\S+?) to (\S+?)\.?\s*$", re.M
)
# Last resort: the title, e.g. "Bump vue-router from 5.3.0 to 5.3.1 in the production-dependencies group".
TITLE_RE = re.compile(r"^Bump (\S+) from (\S+) to (\S+)")
# "Bump the uv-dependencies group with 5 updates": lets us notice when the body lists fewer packages.
TITLE_COUNT_RE = re.compile(r"with (\d+) updates?\b")
VERSION_RE = re.compile(r"^v?(\d+)(?:\.(\d+))?(?:\.(\d+))?")


def gh(*args: str) -> str:
    result = subprocess.run(["gh", *args], capture_output=True, text=True)  # noqa: S603, S607
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        sys.exit(f"`gh {' '.join(args[:2])}` failed with exit code {result.returncode}")
    return result.stdout


def repo_args(repo: str | None) -> list[str]:
    return ["--repo", repo] if repo else []


def bump_level(old: str, new: str) -> tuple[str, str]:
    """Classify a version change. Returns (level, note)."""
    match_old, match_new = VERSION_RE.match(old), VERSION_RE.match(new)
    if not match_old or not match_new:
        return "unknown", "not a semver-style version"
    o = [int(part or 0) for part in match_old.groups()]
    n = [int(part or 0) for part in match_new.groups()]
    if o[0] != n[0]:
        return "major", ""
    if o[1] != n[1]:
        return "minor", "0.x release, may be breaking" if n[0] == 0 else ""
    if o[2] != n[2]:
        return "patch", ""
    return "other", "only the pre-release or build tag changed"


def parse_updates(title: str, body: str) -> list[dict]:
    body = body or ""
    seen: dict[str, dict] = {}
    for m in UPDATES_RE.finditer(body):
        seen.setdefault(m.group(1), {"package": m.group(1), "from": m.group(2), "to": m.group(3)})
    if not seen:
        for m in BUMPS_RE.finditer(body):
            pkg = m.group(1) or m.group(2)
            seen.setdefault(pkg, {"package": pkg, "from": m.group(3), "to": m.group(4)})
    if not seen:
        m = TITLE_RE.match(title or "")
        if m and m.group(1) != "the":
            seen[m.group(1)] = {"package": m.group(1), "from": m.group(2), "to": m.group(3)}
    updates = []
    for update in seen.values():
        level, note = bump_level(update["from"], update["to"])
        updates.append({**update, "bump": level, "note": note})
    updates.sort(key=lambda u: (BUMP_ORDER[u["bump"]], u["package"]))
    return updates


def ci_status(rollup: list[dict] | None) -> tuple[str, list[str]]:
    """Summarise statusCheckRollup as (green|pending|failing|none, details)."""
    if not rollup:
        return "none", []
    failing: list[str] = []
    pending: list[str] = []
    for check in rollup:
        name = check.get("name") or check.get("context") or "unnamed check"
        if check.get("__typename") == "StatusContext":
            state = check.get("state")
            if state in ("PENDING", "EXPECTED"):
                pending.append(name)
            elif state != "SUCCESS":
                failing.append(f"{name} ({state})")
        elif check.get("status") != "COMPLETED":
            pending.append(name)
        elif check.get("conclusion") not in GREEN_CONCLUSIONS:
            failing.append(f"{name} ({check.get('conclusion')})")
    if failing:
        return "failing", failing
    if pending:
        return "pending", pending
    return "green", []


def load_prs(repo: str | None) -> list[dict]:
    fields = "number,title,body,url,headRefOid,createdAt,isDraft,mergeStateStatus,mergeable,statusCheckRollup"
    out = gh(
        "pr",
        "list",
        "--author",
        "app/dependabot",
        "--state",
        "open",
        "--limit",
        "100",
        "--json",
        fields,
        *repo_args(repo),
    )
    return sorted(json.loads(out), key=lambda pr: pr["number"])


def load_repo(repo: str | None) -> dict:
    fields = "nameWithOwner,mergeCommitAllowed,squashMergeAllowed,rebaseMergeAllowed,deleteBranchOnMerge"
    out = gh("repo", "view", *([repo] if repo else []), "--json", fields)
    return json.loads(out)


def merge_method(info: dict) -> str:
    if info.get("mergeCommitAllowed"):
        return "merge"
    if info.get("squashMergeAllowed"):
        return "squash"
    return "rebase"


def analyse(pr: dict) -> dict:
    updates = parse_updates(pr["title"], pr.get("body"))
    ci, ci_details = ci_status(pr.get("statusCheckRollup"))
    merge_state = pr.get("mergeStateStatus") or "UNKNOWN"
    reasons = []
    if pr.get("isDraft"):
        reasons.append("draft")
    if ci == "failing":
        reasons.append("CI failing: " + ", ".join(ci_details))
    elif ci == "pending":
        reasons.append("CI pending: " + ", ".join(ci_details))
    elif ci == "none":
        reasons.append("no CI checks reported")
    if merge_state == "DIRTY" or pr.get("mergeable") == "CONFLICTING":
        reasons.append("merge conflicts")
    if merge_state == "BLOCKED":
        reasons.append("blocked by branch protection")
    warnings = []
    expected = TITLE_COUNT_RE.search(pr["title"] or "")
    if not updates:
        warnings.append("could not parse the package list from the PR body; open the PR before merging")
    elif expected and int(expected.group(1)) != len(updates):
        warnings.append(
            f"title says {expected.group(1)} updates but only {len(updates)} were parsed; open the PR for the rest"
        )
    levels = [u["bump"] for u in updates]
    max_bump = min(levels, key=lambda lvl: BUMP_ORDER[lvl]) if levels else "unknown"
    return {
        "number": pr["number"],
        "title": pr["title"],
        "url": pr["url"],
        "head_sha": pr["headRefOid"],
        "created_at": pr["createdAt"],
        "is_draft": pr.get("isDraft", False),
        "merge_state": merge_state,
        "mergeable": pr.get("mergeable"),
        "ci": ci,
        "ci_details": ci_details,
        "updates": updates,
        "max_bump": max_bump,
        "ready": not reasons,
        "not_ready_reasons": reasons,
        "warnings": warnings,
    }


def bump_summary(updates: list[dict]) -> str:
    counts: dict[str, int] = {}
    for u in updates:
        if u["bump"] != "patch":
            counts[u["bump"]] = counts.get(u["bump"], 0) + 1
    if not updates:
        return "could not parse"
    if not counts:
        return "patch only"
    return ", ".join(f"{counts[lvl]} {lvl}" for lvl in sorted(counts, key=lambda lvl: BUMP_ORDER[lvl]))


def ci_cell(pr: dict) -> str:
    if pr["ci"] == "green":
        return "green"
    if pr["ci"] == "none":
        return "no checks"
    return f"{pr['ci'].upper()}: " + ", ".join(pr["ci_details"])


def render(info: dict, method: str, prs: list[dict]) -> str:
    lines = [f"# Dependabot review for {info['nameWithOwner']}", ""]
    if not prs:
        lines.append("No open Dependabot PRs. Nothing to do.")
        return "\n".join(lines) + "\n"

    lines += [
        f"{len(prs)} open Dependabot PR(s).",
        "",
        "| PR | Title | CI | Merge state | Bumps above patch |",
        "|---|---|---|---|---|",
    ]
    for pr in prs:
        lines.append(
            f"| #{pr['number']} | {pr['title']} | {ci_cell(pr)} | {pr['merge_state']} | {bump_summary(pr['updates'])} |"
        )

    lines += ["", "## Upgrades larger than a patch release, by PR", ""]
    patch_only: list[dict] = []
    for pr in prs:
        above_patch = [u for u in pr["updates"] if u["bump"] != "patch"]
        if not above_patch:
            patch_only.append(pr)
            continue
        lines += [
            f"### #{pr['number']} {pr['title']}",
            pr["url"],
            "",
            "| Package | From | To | Bump |",
            "|---|---|---|---|",
        ]
        for u in above_patch:
            level = f"**{u['bump'].upper()}**" if u["bump"] == "major" else u["bump"]
            note = f" ({u['note']})" if u["note"] else ""
            lines.append(f"| {u['package']} | {u['from']} | {u['to']} | {level}{note} |")
        patches = [u for u in pr["updates"] if u["bump"] == "patch"]
        if patches:
            lines.append("")
            lines.append(
                "Patch-level in this PR: " + ", ".join(f"{u['package']} {u['from']} to {u['to']}" for u in patches)
            )
        lines.append("")
    if patch_only:
        lines.append("### PRs with only patch-level bumps")
        for pr in patch_only:
            pkgs = (
                ", ".join(f"{u['package']} {u['from']} to {u['to']}" for u in pr["updates"])
                or "could not parse packages"
            )
            lines.append(f"- #{pr['number']} {pr['title']}: {pkgs}")
        lines.append("")

    noted = [pr for pr in prs if pr["warnings"]]
    if noted:
        lines += ["## Notes", ""]
        for pr in noted:
            lines += [f"- #{pr['number']}: {warning}" for warning in pr["warnings"]]
        lines.append("")

    ready = [pr for pr in prs if pr["ready"]]
    held = [pr for pr in prs if not pr["ready"]]
    lines += ["## Merge readiness", ""]
    lines.append("- Ready to merge (CI green): " + (", ".join(f"#{pr['number']}" for pr in ready) or "none"))
    patch_ready = [pr for pr in ready if pr["max_bump"] == "patch"]
    lines.append("- Ready and patch-only: " + (", ".join(f"#{pr['number']}" for pr in patch_ready) or "none"))
    if held:
        lines.append("- Held back:")
        for pr in held:
            lines.append(f"  - #{pr['number']}: " + "; ".join(pr["not_ready_reasons"]))
    else:
        lines.append("- Held back: none")
    lines.append(f"- Merge method for this repo: --{method}")
    if ready:
        numbers = " ".join(str(pr["number"]) for pr in ready)
        lines.append(f"- Merge command: merge_dependabot.py {numbers}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", help="OWNER/NAME; defaults to the repo of the current directory")
    parser.add_argument("--json", dest="json_path", help="also write the report data as JSON to this path")
    args = parser.parse_args()

    info = load_repo(args.repo)
    method = merge_method(info)
    prs = [analyse(pr) for pr in load_prs(args.repo)]
    sys.stdout.write(render(info, method, prs))

    if args.json_path:
        data = {
            "repo": info["nameWithOwner"],
            "merge_method": method,
            "prs": prs,
            "ready": [pr["number"] for pr in prs if pr["ready"]],
            "ready_patch_only": [pr["number"] for pr in prs if pr["ready"] and pr["max_bump"] == "patch"],
            "held_back": [pr["number"] for pr in prs if not pr["ready"]],
        }
        with open(args.json_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
