# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django Base Site is an opinionated Django starter template that provides a production-ready foundation with modern tooling and best practices. It uses Django 5 with a custom user model, Celery for background tasks, and includes authentication via Django Allauth.

## Architecture

- **Apps Structure**: Located in `apps/` directory with `accounts/` (custom user model) and `base/` (core utilities)
- **Configuration**: Settings split into modules in `config/settings/` with environment-based configuration via Environs
- **Frontend**: Vite-based build system with Bootstrap 5, assets in `src/` directory
- **Docker**: Multi-stage production Dockerfile with development compose setup using Docker Desktop
- **Static Files**: Custom storage backend in `apps/base/storage.py`, collected to `collected_static/`

## Development Commands

Use Just for all development tasks. Key commands:

**Setup & Management:**
- `just start` - Start Docker Compose development environment
- `just build` - Build Docker images and collect static files
- `just stop` - Stop all services
- `just clean` - Remove build files and cache

**Code Quality:**
- `just format` - Format all code (Python with Ruff, JS with ESLint, SASS with Stylelint, HTML with djLint)
- `just lint` - Lint everything (includes type checking with ty)
- `just pre_commit` - Run format, lint, and test pipeline

**Testing:**
- `just test` - Run pytest without coverage
- `just test_with_coverage` - Run tests with coverage report

**Asset Building:**
- `just build_frontend` - Build frontend assets with Vite
- `just collectstatic` - Run Django's collectstatic

**Dependencies:**
- `just upgrade_python_packages` - Upgrade Python deps using uv
- `just upgrade_node_packages` - Upgrade Node deps

## Testing

- Uses pytest with pytest-django plugin
- Test settings in `config.settings.test_runner`
- Model Bakery for test data generation
- Django Test Plus for additional test helpers
- Coverage configuration in `config/coverage.ini`

## Code Standards

- **Python**: Formatted with Ruff, type-checked with ty, follows Django conventions
- **JavaScript**: ESLint with Airbnb base config
- **SASS/CSS**: Stylelint with standard SCSS config and recess order
- **HTML**: djLint for Django template formatting and linting
- **Line Length**: 120 characters for Python and HTML

## Debugging

The project supports remote debugging with VS Code, LazyVim/Neovim, or any DAP-compatible editor.

**Enable Debugging:**
1. Set `ENABLE_DEBUGGER=true` in your `.env` file, OR
2. Uncomment the `ENABLE_DEBUGGER` line in `compose.yml`, OR
3. Run: `ENABLE_DEBUGGER=true docker compose up`

**VS Code:**
- Use the "Django: Attach to Docker" configuration in `.vscode/launch.json`
- Start the containers with debugging enabled
- Press F5 or Run > Start Debugging
- Set breakpoints in your Python code

**LazyVim/Neovim:**
- Configure nvim-dap to connect to `localhost:5678`
- The debugger uses the standard Debug Adapter Protocol (DAP)

**Notes:**
- Debugger listens on port 5678
- Auto-reload is disabled when debugging is enabled
- Restart the server manually after code changes when debugging

## Environment Configuration

Uses `.env` file for local development with these key variables:
- `DEBUG=on` for development
- `SECRET_KEY` - Django secret key
- `DATABASE_URL` - PostgreSQL connection string
- `INTERNAL_IPS` - For Django Debug Toolbar
- `ENABLE_DEBUGGER=true` - Enable remote debugging (optional)

## Key Dependencies

- **Backend**: Django 5, Celery, Redis, PostgreSQL, Django Allauth, Crispy Forms
- **Frontend**: Vite, Bootstrap 5, SASS
- **Development**: Docker, pytest, Ruff, ty, ESLint, Stylelint
