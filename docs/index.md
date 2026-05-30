---
title: Overview
---

# Django Base Site

--8<-- "README.md:intro"

--8<-- "README.md:readme"

## Working on the Documentation

These docs are built with [Zensical](https://zensical.org/).

Use the following Just commands:

```bash
just docs          # Serve locally at http://localhost:4000
just docs-build    # Build the static site into docs_site/
just docs-lint     # Check for broken links
```

You can also run the underlying commands directly:

```bash
uv run zensical serve -f zensical.toml
uv run zensical build -f zensical.toml --clean
```

Output is written to the `docs_site/` directory.
