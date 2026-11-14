"""compose.yml must let a git worktree run its own copy of the stack beside the main checkout's (scripts/worktree)."""

import re

from django.conf import settings

COMPOSE_FILE = settings.BASE_DIR / "compose.yml"
HOST_PORT_VARIABLE = re.compile(r"\$\{(HOST_PORT_[A-Z0-9_]+):-(\d+)\}")


def published_ports(compose_text: str) -> list[str]:
    """Each entry of every `ports:` list, without its dash, quotes, or trailing comment."""
    ports = []
    list_indent = None
    for line in compose_text.splitlines():
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if stripped == "ports:":
            list_indent = indent
        elif list_indent is not None and stripped.startswith("- ") and indent > list_indent:
            ports.append(stripped[2:].split("#")[0].strip().strip("'\""))
        elif stripped and not stripped.startswith("#"):
            list_indent = None
    return ports


class TestComposeFile:
    def test_services_have_no_fixed_container_names(self):
        # A second stack can't start while a container with the same name exists.
        assert "container_name:" not in COMPOSE_FILE.read_text()

    def test_every_published_port_is_a_host_port_variable(self):
        # scripts/worktree moves each worktree's stack to free ports by setting these variables in its .env.
        ports = published_ports(COMPOSE_FILE.read_text())
        assert ports
        for port in ports:
            assert re.fullmatch(r"(127\.0\.0\.1:)?\$\{HOST_PORT_[A-Z0-9_]+:-\d+\}:\d+", port), port

    def test_each_host_port_variable_has_one_default(self):
        # scripts/worktree reads the defaults from this file, so one variable can't have two.
        defaults: dict[str, set[str]] = {}
        for variable, default in HOST_PORT_VARIABLE.findall(COMPOSE_FILE.read_text()):
            defaults.setdefault(variable, set()).add(default)
        assert {variable: values for variable, values in defaults.items() if len(values) > 1} == {}
