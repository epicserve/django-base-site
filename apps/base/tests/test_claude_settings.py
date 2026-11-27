"""`.claude/settings.json` holds the permission rules that stop Claude Code running destructive commands."""

import json
import re

from django.conf import settings

SETTINGS_FILE = settings.BASE_DIR / ".claude" / "settings.json"
RULE_LISTS = ("allow", "ask", "deny")


def permission_rules() -> list[str]:
    permissions = json.loads(SETTINGS_FILE.read_text())["permissions"]
    return [rule for key in RULE_LISTS for rule in permissions.get(key, [])]


class TestClaudeSettings:
    def test_is_valid_json(self):
        # Claude Code skips a settings file it can't parse, and a `claude -p` run says nothing about it, so one trailing
        # comma would silently drop every rule.
        assert isinstance(json.loads(SETTINGS_FILE.read_text()), dict)

    def test_rules_are_well_formed(self):
        # Claude Code skips a malformed rule with only a warning, so the command it was meant to stop runs unasked.
        rules = permission_rules()
        assert rules
        for rule in rules:
            match = re.fullmatch(r"(?P<tool>[A-Za-z]+)\((?P<specifier>.+)\)", rule)
            assert match, rule
            specifier = match["specifier"]
            # `:*` is a wildcard only at the end; anywhere else the colon is literal and the rule never matches.
            assert ":*" not in specifier[:-2], rule
            # A rule on Bash's `command` parameter would be bypassed by a compound command, so Claude Code ignores it.
            assert not specifier.startswith("command:"), rule

    def test_worktrees_go_through_worktrunk(self):
        # Claude Code makes its own worktrees (`--worktree`, subagents with `isolation: "worktree"`) with
        # `git worktree add`, which skips Worktrunk's hooks, so the worktree has no .env and its stack would use the
        # main checkout's ports. Worktrunk's plugin replaces that with `wt switch --create` through Claude Code's
        # WorktreeCreate and WorktreeRemove hooks.
        claude_settings = json.loads(SETTINGS_FILE.read_text())
        marketplace = claude_settings["extraKnownMarketplaces"]["worktrunk"]["source"]
        assert marketplace == {"source": "github", "repo": "max-sixty/worktrunk"}
        assert claude_settings["enabledPlugins"]["worktrunk@worktrunk"] is True
