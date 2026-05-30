---
title: Overview
---

# Django Base Site

--8<-- "README.md:intro"

--8<-- "README.md:readme"

## Documentation

| Page | Description |
|------|-------------|
| [Docker](docker.md) | Local development with Docker Compose, services, volumes, and common gotchas. |
| [Debugging](debugging.md) | Remote debugging with VS Code, PyCharm, Neovim, and other DAP clients. |
| [S3 / MinIO](s3.md) | Media storage setup using MinIO locally and S3-compatible providers in production. |
| [Billing](billing.md) | Opt-in Stripe subscriptions, feature gating, and per-seat pricing (disabled by default). |
| [Website Launch Checklist](website-launch-checklist.md) | Pre-launch tasks and production readiness items. |
| [Changelog](changelog.md) | Full project changelog. |

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
