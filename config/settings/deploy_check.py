"""
Settings for `just lint_deploy`, which runs `manage.py check --deploy` against the production defaults.

The HTTPS settings in _base.py are worked out from DEBUG when it's imported, so the recipe sets the production-like
environment (DEBUG off, no .env) rather than this module. This module only silences the checks the template can't pass,
so `check --deploy` in a real deploy, under `config.settings`, still shows them.
"""

from ._base import *  # noqa: F403

SILENCED_SYSTEM_CHECKS = [
    # SECURE_HSTS_INCLUDE_SUBDOMAINS. It makes browsers use HTTPS for every subdomain of the site's domain, including
    # ones this app doesn't serve, and the template can't know what those are.
    "security.W005",
    # SECURE_HSTS_PRELOAD. Preloading needs includeSubDomains and a submission to browsers' preload lists, and getting
    # off them takes months, so it's each project's decision for its own domain.
    "security.W021",
]
