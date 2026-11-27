"""`just test_e2e` runs scripts/pytest_e2e: the e2e tests it's given, or all of e2e/ when it's given none."""

import os
import subprocess

from django.conf import settings

import pytest

SCRIPT = settings.BASE_DIR / "scripts" / "pytest_e2e"


def pytest_args(*args):
    """Return the arguments the script passes to pytest, read back through an `echo` prefix in place of Docker's."""
    env = {**os.environ, "PYTHON_CMD_PREFIX": "echo"}
    result = subprocess.run([SCRIPT, *args], capture_output=True, text=True, env=env, check=True)  # noqa: S603 (runs this repo's own script with test-chosen arguments)
    return result.stdout.split()


class TestPytestE2EScript:
    @pytest.mark.parametrize(
        "args",
        [
            [],
            ["-x"],
            ["-n", "4"],
            ["-k", "avatar"],
            ["--deselect", "e2e/test_avatar.py::test_upload"],
        ],
    )
    def test_runs_whole_suite_without_a_path(self, args):
        assert pytest_args(*args) == ["pytest", "e2e/", "--ds=config.settings.e2e", *args]

    @pytest.mark.parametrize(
        "args",
        [
            ["e2e/test_avatar.py"],
            ["e2e/test_avatar.py::TestAvatar::test_upload"],
            ["e2e/test_avatar.py", "e2e/test_auth.py"],
            ["-n", "4", "e2e/test_avatar.py", "-x"],
        ],
    )
    def test_runs_only_the_paths_given(self, args):
        assert pytest_args(*args) == ["pytest", "--ds=config.settings.e2e", *args]
