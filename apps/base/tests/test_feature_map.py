"""The run-app skill's feature map (`.agents/skills/run-app/features/`) must keep up with the SPA and the e2e suite."""

import re

from django.conf import settings

SKILL_DIR = settings.BASE_DIR / ".agents" / "skills" / "run-app"
FEATURES_DIR = SKILL_DIR / "features"
ROUTER = settings.BASE_DIR / "frontend" / "js" / "router.ts"
# Spelled with its directory: the template's install-script job fails on a bare reference to the template's own
# top-level readme, which new projects don't have.
README = SKILL_DIR / "features/README.md"


def feature_files():
    return sorted(path for path in FEATURES_DIR.glob("*.md") if path != README)


def map_text():
    return "\n".join(path.read_text() for path in FEATURES_DIR.glob("*.md"))


def route_names():
    return re.findall(r"\bname: '([^']+)'", ROUTER.read_text())


class TestFeatureMap:
    def test_every_route_is_in_a_feature_file(self):
        # An agent given a bug report goes from the screen to its feature file by route, so a route no file names is a
        # page the map can't lead it to. Name it in backticks (`login`) in the file for its feature.
        names = route_names()
        assert len(names) > 20, "router.ts has fewer named routes than expected; has its format changed?"
        text = "\n".join(path.read_text() for path in feature_files())
        missing = [name for name in names if f"`{name}`" not in text]
        assert missing == [], f"Add these routes to a file in {FEATURES_DIR.relative_to(settings.BASE_DIR)}/"

    def test_readme_lists_every_feature_file(self):
        readme = README.read_text()
        unlisted = [path.name for path in feature_files() if f"]({path.name})" not in readme]
        assert unlisted == []

    def test_relative_links_resolve(self):
        broken = [
            f"{path.name}: {target}"
            for path in FEATURES_DIR.glob("*.md")
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text())
            if not re.match(r"(https?:|mailto:|#)", target) and not (path.parent / target.split("#")[0]).exists()
        ]
        assert broken == []

    def test_named_e2e_tests_exist(self):
        # The map names the e2e tests that cover each flow. A renamed or deleted test would send an agent looking for
        # coverage that isn't there.
        references = set(re.findall(r"`(e2e/test_\w+\.py)(?:::(\w+))?`", map_text()))
        assert references
        missing = []
        for file, test in sorted(references):
            path = settings.BASE_DIR / file
            if not path.exists():
                missing.append(file)
            elif test and not re.search(rf"\bdef {test}\(", path.read_text()):
                missing.append(f"{file}::{test}")
        assert missing == []
