# Recipes for the Django Base Site documentation site (docs/, built with Zensical).
#
# Template-only: `just clean_extra_files` deletes this file along with docs/ when
# scripts/start_new_project creates a new project, and the justfile loads it with
# `import?` so the recipes disappear cleanly instead of failing.

# Serve documentation locally with Zensical (on port 4000)
@docs:
    uv run zensical serve -f zensical.toml

# Build the documentation site (outputs to docs_site/)
@docs-build:
    uv run zensical build -f zensical.toml --clean --strict

# Lint documentation links
@docs-lint: lint_docs

# Lint docs links
@lint_docs:
    just _start_msg "Validate internal docs links (Zensical strict build)"
    uv run zensical build -f zensical.toml --strict
    just _start_msg "Check external documentation links"
    # Zensical's strict build above owns internal links (it validates with the renderer's
    # own resolution rules), so the first --exclude skips every non-http link —
    # mkdocs-linkcheck resolves local links directory-URL style and false-positives
    # source-relative .md links that Zensical renders correctly.
    # Second --exclude: GitHub throttles the checker's rapid requests, randomly failing
    # valid links to our own repo. Third-party URLs are still checked.
    {{ python_cmd_prefix }} mkdocs-linkcheck ./docs --exclude '^(?!https?://)' --exclude 'github\.com/epicserve/django-base-site/blob/'
