# Recipes for maintaining the Django Base Site template itself.
#
# Template-only: `just clean_extra_files` deletes this file (and so itself) when
# scripts/start_new_project creates a new project, and the justfile loads it with
# `import?` so the recipe disappears instead of lingering, broken, in the new project.

# Remove extra Django Base Site files not needed in a new project. Keeps the project CI
# (.github/workflows/ci.yml) and Dependabot config; drops the template-only workflow, the
# docs site and its dev dependencies, AGENTS.md's template-only blocks, and this recipe.
clean_extra_files:
    #!/usr/bin/env bash
    set -euo pipefail
    command -v uv >/dev/null 2>&1 || { echo "uv is required to remove the docs site's dev dependencies — https://docs.astral.sh/uv/"; exit 1; }
    # First, so a failure leaves the tree untouched. Updates pyproject.toml and uv.lock.
    uv remove --dev --no-sync zensical mkdocs-linkcheck
    rm -f LICENSE.md
    rm -f README.md
    rm -f CHANGELOG.md
    rm -rf docs/
    rm -f config/docs.just
    rm -f zensical.toml
    rm -f .github/workflows/template.yml
    rm -f .readthedocs.yaml
    rm -f scripts/start_new_project
    sed -i.bak '/^<!-- template-only:start -->$/,/^<!-- template-only:end -->$/d' AGENTS.md && rm AGENTS.md.bak
    rm -f config/template.just
