# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Budgeteer is a Django 5 web application built on the Django Base Site template. It uses a custom user model, Celery for background tasks, and Django Allauth for authentication. All development tasks run inside Docker via Just.

## Architecture

- **Apps**: `apps/accounts/` (custom user model, Allauth adapter, signin/name-change views) and `apps/base/` (Vite template tag, context processors, custom storage, Celery tasks)
- **Config**: `config/settings/_base.py` (shared), `config/settings/test_runner.py` (test overrides); environment loaded via Environs from `.env`
- **URLs**: root (`/`) is login-required index; `/accounts/` is Allauth; `/-/` is health checks; debug toolbar at `/__debug__/` in dev
- **Frontend**: Vite build system outputs to `public/static/dist/`; `apps/base/` provides a custom `{% vite %}` template tag for asset injection; Bootstrap 5 + SASS in `src/`
- **Static Files**: custom storage backend at `apps/base/storage.py`; collected to `collected_static/`
- **Docker Services**: `web` (Django, port 8000), `db` (PostgreSQL), `redis`, `node` (Vite dev server, port 3000), `worker` (Celery); `just start_full` adds docs (MkDocs, port 4000)

## Development Commands

All commands run inside Docker containers by default. Override with `PYTHON_CMD_PREFIX` / `NODE_CMD_PREFIX` env vars to run locally.

**Setup & Management:**
- `just start` - Start Docker Compose environment
- `just start_full` - Start with full profile (includes docs server)
- `just build` - Build Docker images and collect static files
- `just stop` - Stop all services
- `just clean` - Remove build artifacts, caches, coverage data

**Code Quality:**
- `just format` - Format all code (Ruff, ESLint, Stylelint, djLint, justfile)
- `just lint` - Lint everything including migrations check and mypy
- `just pre_commit` - Run format → lint → test pipeline

**Testing:**
- `just test` - Run pytest
- `just test_with_coverage` - Run tests with coverage HTML report
- Run a single test: `docker compose exec web pytest --ds=config.settings.test_runner path/to/test.py::TestClass::test_method`

**Asset Building:**
- `just build_frontend` - Build frontend assets with Vite
- `just collectstatic` - Run Django's collectstatic

**Database:**
- `just db_dump` - Dump database to `~/Downloads/`
- `just db_restore [dump_file]` - Restore from dump (defaults to latest in `~/Downloads/`)

**Dependencies:**
- `just upgrade_python_packages [pkg...]` - Upgrade all or specific Python packages via uv
- `just upgrade_node_packages` - Upgrade Node packages
- `just upgrade_all_packages` - Upgrade both, rebuild, and run pre-commit

## Testing

- pytest + pytest-django; settings module: `config.settings.test_runner`
- Model Bakery for fixture-free test data; Django Test Plus for extra helpers
- Coverage config: `config/coverage.ini`

## Code Standards

- **Python**: Ruff (format + lint), mypy strict type checking; 120-char line length
- **JavaScript**: ESLint with Airbnb base config
- **SASS/CSS**: Stylelint with standard SCSS + recess order
- **HTML**: djLint; 120-char line length, 2-space indent

## Environment Configuration

`.env` file for local development:
- `DEBUG=on`
- `SECRET_KEY`
- `DATABASE_URL` - PostgreSQL connection string
- `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB`
- `INTERNAL_IPS` - For Django Debug Toolbar

## Key Dependencies

- **Backend**: Django 5, Celery, Redis, PostgreSQL, Django Allauth, Crispy Forms, django-alive (health checks), django-maintenance-mode
- **Frontend**: Vite, Bootstrap 5, SASS
- **Development**: Docker, pytest, Ruff, mypy, ESLint, Stylelint, uv
