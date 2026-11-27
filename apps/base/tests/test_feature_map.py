"""The run-app skill's feature map (`.agents/skills/run-app/features/`) must keep up with the SPA and the e2e suite."""

import ast
import re

from django.conf import settings

SKILLS_DIR = settings.BASE_DIR / ".agents" / "skills"
SKILL_DIR = SKILLS_DIR / "run-app"
FEATURES_DIR = SKILL_DIR / "features"
ROUTER = settings.BASE_DIR / "frontend" / "js" / "router.ts"
# Spelled with its directory: the template's install-script job fails on a bare reference to the template's own
# top-level readme, which new projects don't have.
README = SKILL_DIR / "features/README.md"
# A path the map names in backticks starts with one of these. Route fragments such as `members/` don't.
SOURCE_ROOTS = ("apps/", "config/", "e2e/", "frontend/", "scripts/")


def feature_files():
    return sorted(path for path in FEATURES_DIR.glob("*.md") if path != README)


def map_text():
    return "\n".join(path.read_text() for path in FEATURES_DIR.glob("*.md"))


def route_names():
    return re.findall(r"\bname: '([^']+)'", ROUTER.read_text())


def backticked(text):
    return re.findall(r"`([^`\s]+)`", text)


def node_id_error(node_id, root=settings.BASE_DIR):
    """Say why pytest wouldn't find the e2e test `node_id` (`e2e/test_x.py::TestClass::test_y`), or "" if it would."""
    file, *names = node_id.split("::")
    if not re.fullmatch(r"e2e/[\w/]+\.py", file):
        return "name an e2e test as e2e/<file>.py::<Class>::<test>"
    path = root / file
    if not path.is_file():
        return f"{file} doesn't exist"
    if not names or len(names) > 2:
        return "name a class, a test function, or a class and its test method"
    definitions = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    top_level = {node.name: node for node in ast.parse(path.read_text()).body if isinstance(node, definitions)}
    owner = top_level.get(names[0])
    if owner is None:
        classes = [
            name for name, node in top_level.items() if isinstance(node, ast.ClassDef) and names[0] in methods(node)
        ]
        return f"name its class: {file}::{classes[0]}::{names[0]}" if classes else f"{file} has no {names[0]}"
    if len(names) == 2 and not (isinstance(owner, ast.ClassDef) and names[1] in methods(owner)):
        return f"{names[0]} has no method {names[1]}"
    return ""


def methods(cls):
    return {node.name for node in cls.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


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
        # Every skill, not just the map: fix-bug sends an agent through run-app and the map by relative link.
        broken = [
            f"{path.relative_to(SKILLS_DIR)}: {target}"
            for path in SKILLS_DIR.rglob("*.md")
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text())
            if not re.match(r"(https?:|mailto:|#)", target) and not (path.parent / target.split("#")[0]).exists()
        ]
        assert broken == []

    def test_named_paths_exist(self):
        # The map points at the source and tests behind each feature. A moved or deleted file would send an agent to
        # read code that isn't there.
        paths = {token.split("::")[0] for token in backticked(map_text()) if token.startswith(SOURCE_ROOTS)}
        assert len(paths) > 20, "the map names fewer paths than expected; has the backtick format changed?"
        missing = sorted(path for path in paths if not (settings.BASE_DIR / path).exists())
        assert missing == []

    def test_named_e2e_tests_exist(self):
        # The map names the e2e tests that cover each flow, by pytest node ID. A renamed or deleted test would send an
        # agent looking for coverage that isn't there.
        node_ids = {token for token in backticked(map_text()) if "::" in token}
        assert len(node_ids) > 5, "the map names fewer e2e tests than expected; has the backtick format changed?"
        errors = {node_id: error for node_id in sorted(node_ids) if (error := node_id_error(node_id))}
        assert errors == {}

    def test_node_id_error(self, tmp_path, subtests):
        (tmp_path / "e2e").mkdir()
        (tmp_path / "e2e" / "test_x.py").write_text(
            "class TestA:\n    def test_a(self): ...\n\n"
            "class TestB:\n    def test_b(self): ...\n\n"
            "def test_function(): ...\n"
        )
        cases = [
            ("e2e/test_x.py::TestA", ""),
            ("e2e/test_x.py::TestA::test_a", ""),
            ("e2e/test_x.py::test_function", ""),
            ("e2e/test_missing.py::TestA::test_a", "e2e/test_missing.py doesn't exist"),
            ("e2e/test_x.py::TestMissing::test_a", "e2e/test_x.py has no TestMissing"),
            ("e2e/test_x.py::TestA::test_missing", "TestA has no method test_missing"),
            ("e2e/test_x.py::TestB::test_a", "TestB has no method test_a"),
            ("e2e/test_x.py::test_a", "name its class: e2e/test_x.py::TestA::test_a"),
            ("e2e/test_x.py::test_function::test_a", "test_function has no method test_a"),
            ("TestA::test_a", "name an e2e test as e2e/<file>.py::<Class>::<test>"),
            ("e2e/test_x.py::TestA::test_a::extra", "name a class, a test function, or a class and its test method"),
        ]
        for node_id, error in cases:
            with subtests.test(node_id):
                assert node_id_error(node_id, root=tmp_path) == error
