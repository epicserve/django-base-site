"""
Hold the test suite to the style in AGENTS.md's Testing section.

A test class that touches the database is a `BaseTest` with `setUpTestData`, so it builds its rows once for the class
rather than once per test, and a test that doesn't is a plain class. A module-level test function or a `django_db` mark
is the pattern that builds data per test, so neither is allowed under `apps/`.
"""

import ast
from pathlib import Path

from django.conf import settings

TEST_FILES = sorted((Path(settings.BASE_DIR) / "apps").glob("*/tests/**/test_*.py"))


def _relative(path: Path) -> str:
    return str(path.relative_to(settings.BASE_DIR))


def _is_django_db_mark(node: ast.AST) -> bool:
    # `pytest.mark.django_db`, with or without arguments.
    target = node.func if isinstance(node, ast.Call) else node
    return isinstance(target, ast.Attribute) and target.attr == "django_db"


class TestTestStyle:
    def test_finds_the_test_files(self):
        assert len(TEST_FILES) > 10

    def test_no_module_level_test_functions(self):
        offenders = [
            f"{_relative(path)}:{node.lineno} {node.name}"
            for path in TEST_FILES
            for node in ast.parse(path.read_text()).body
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test")
        ]

        assert offenders == [], "Group tests in a class (see AGENTS.md's Testing section)"

    def test_no_django_db_marks(self):
        offenders = [
            f"{_relative(path)}:{node.lineno}"
            for path in TEST_FILES
            for node in ast.walk(ast.parse(path.read_text()))
            if _is_django_db_mark(node)
        ]

        assert offenders == [], "A test class that uses the database subclasses BaseTest and uses setUpTestData"
