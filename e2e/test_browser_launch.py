import os
from pathlib import Path

import pytest
from playwright.sync_api import Playwright

PROC = Path("/proc")

# Chromium 147 adds these to its own environment, FC_FONTATIONS after its threads have started, which can crash it at
# launch on glibc before 2.41. e2e/conftest.py sets them first, so Chromium only overwrites them.
NAMES_CHROMIUM_ADDS = {"FC_FONTATIONS", "DBUS_SESSION_BUS_ADDRESS"}


def _parent_pid(pid: int) -> int:
    # The process name in /proc/<pid>/stat can hold spaces and parentheses, so split after its closing one.
    return int((PROC / str(pid) / "stat").read_text().rsplit(")", 1)[1].split()[1])


def _descends_from(pid: int, ancestor: int) -> bool:
    while pid > 1:
        if pid == ancestor:
            return True
        pid = _parent_pid(pid)
    return False


def _driver_pids() -> list[int]:
    """Return the Playwright driver processes started by this test process."""
    pids = []
    for path in PROC.glob("[0-9]*"):
        try:
            if b"run-driver" in (path / "cmdline").read_bytes().split(b"\0") and _descends_from(
                int(path.name), os.getpid()
            ):
                pids.append(int(path.name))
        except OSError:
            continue  # The process exited while we looked at it.
    return pids


def _environment_names(pid: int) -> set[str]:
    """Return the names in a process's environment when it started; later setenv() calls don't show up here."""
    entries = (PROC / str(pid) / "environ").read_bytes().split(b"\0")
    return {entry.split(b"=", 1)[0].decode() for entry in entries if entry}


@pytest.mark.skipif(not PROC.is_dir(), reason="reads the driver's environment from /proc, which only Linux has")
class TestBrowserLaunch:
    def test_driver_starts_with_the_variables_chromium_would_add(self, playwright: Playwright):
        # The driver launches Chromium with its own environment. Chromium's /proc/<pid>/environ can't be checked
        # instead: once these names are set, Chromium writes its process title over that memory.
        pids = _driver_pids()
        assert pids, "found no Playwright driver process started by this test run"
        for pid in pids:
            assert _environment_names(pid) >= NAMES_CHROMIUM_ADDS
