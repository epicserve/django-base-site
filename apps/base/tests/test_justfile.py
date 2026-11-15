"""The just recipes must act on this checkout's Docker volumes, never another checkout's (scripts/worktree)."""

from django.conf import settings

JUSTFILES = [settings.BASE_DIR / "justfile", *sorted((settings.BASE_DIR / "config").glob("*.just"))]


class TestJustfile:
    def test_volume_commands_dont_use_project_slug(self):
        # project_slug names the main checkout's Compose project. A git worktree's is <slug>-<branch>, so in a worktree
        # `{{ project_slug }}_node_modules` is the main checkout's volume, and `grep {{ project_slug }}` matches every
        # worktree's volumes as well. Use the checkout's own project name (`just _compose_project`) instead.
        offending = [
            f"{path.name}: {line.strip()}"
            for path in JUSTFILES
            for line in path.read_text().splitlines()
            if "docker volume" in line and "project_slug" in line
        ]
        assert offending == []
