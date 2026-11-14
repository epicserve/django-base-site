"""Every environment variable the settings read must be declared in .env.toml, epicenv's schema."""

import re
import tomllib

from django.conf import settings

SETTINGS_DIR = settings.BASE_DIR / "config" / "settings"
SCHEMA_FILE = settings.BASE_DIR / ".env.toml"
# env("NAME", ...), env.bool("NAME", ...), env.list("NAME", ...), and so on.
ENV_CALL = re.compile(r"""\benv(?:\.[a-z_]+)?\(\s*["']([A-Z][A-Z0-9_]*)["']""")


class TestEnvSchema:
    def test_settings_only_read_declared_variables(self):
        # epicenv raises UndefinedVariableError for an undeclared variable whenever it isn't set, even with a default.
        # A .env usually sets them, so this only showed up where there's none: CI's native lint job (#1387).
        read = {name for path in SETTINGS_DIR.glob("*.py") for name in ENV_CALL.findall(path.read_text())}
        declared = set(tomllib.loads(SCHEMA_FILE.read_text())["variables"])
        assert read
        assert sorted(read - declared) == []
