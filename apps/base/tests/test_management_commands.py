"""
Every project management command must import cleanly.

`ty` ignores unresolved imports, so a command that imports a package missing
from the lockfile only fails when someone runs it. `create_fake_users` did
exactly that with `faker` (#1365). Loading each command here turns that into a
test failure.
"""

from django.core.management import get_commands, load_command_class

import pytest

PROJECT_COMMANDS = sorted((name, app) for name, app in get_commands().items() if app.startswith("apps."))


class TestManagementCommandsImport:
    def test_project_commands_are_discovered(self):
        names = {name for name, _app in PROJECT_COMMANDS}
        assert {"ensure_s3_bucket", "purge_notifications", "seed_dev"} <= names

    @pytest.mark.parametrize(("name", "app"), PROJECT_COMMANDS, ids=[name for name, _app in PROJECT_COMMANDS])
    def test_command_imports(self, name, app):
        load_command_class(app, name)
