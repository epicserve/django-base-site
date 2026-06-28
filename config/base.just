# This is base Just file that is used to keep all common commands across projects.
#
# Documentation: https://github.com/casey/just
# Use docker compose as the default prefix for commands. Set these environment variables to an empty string to overwrite
# running with docker-compose.

python_cmd_prefix := env_var_or_default('PYTHON_CMD_PREFIX', 'docker compose exec web')
python_cmd_prefix_with_deps := env_var_or_default('PYTHON_CMD_PREFIX_WITH_DEPS', 'docker compose exec web')
bun_cmd_prefix := env_var_or_default('BUN_CMD_PREFIX', 'docker compose run --no-deps --rm -e NODE_ENV=production frontend')

set dotenv-load := true

# COLORS

green := `tput -Txterm setaf 2`
reset := `tput -Txterm sgr0`

@_green message:
    echo "{{ green }}{{ message }}{{ reset }}"

@_start_msg msg:
    just _green "{{ msg }} ..."

# Start the web service (and its deps) if it isn't already running, when using the Docker prefix
_ensure_web:
    #!/usr/bin/env bash
    if [[ "{{ python_cmd_prefix }}" != docker* ]]; then
        exit 0
    fi
    if [ -z "$(docker compose ps --status running -q web)" ]; then
        just _start_msg "Starting the web service"
        docker compose up --wait -d web
    fi

# Build Docker images
@build:
    just _start_msg "Building docker project"
    docker volume rm {{ project_slug }}_node_modules || true
    docker compose build
    just collectstatic

# Build frontend assets
@build_frontend:
    {{ bun_cmd_prefix }} bun run build
    just collectstatic

# Remove build files, python cache files and test coverage data
@clean: clean_py_cache clean_coverage_data
    rm -rf .ty_cache/
    rm -rf .pytest_cache/
    rm -rf .ruff_cache/
    rm -rf collected_static/
    rm -rf docs_site/
    rm -rf public/static/dist/
    rm -rf .coverage

# Remove Django test coverage data
@clean_coverage_data:
    rm -f .coverage
    rm -rf htmlcov

# Kill and remove all docker containers
@clean_docker_containers:
    # kill all stopped containers
    stopped_containers=$(docker ps | awk '{if (NR!=1) {print $1}}'); \
    if [[ -n $stopped_containers ]]; then \
        docker kill $stopped_containers; \
    fi \
    # remove all containers
    containers=$(docker ps -a -q); \
    if [[ -n $containers ]]; then \
        docker rm $containers; \
    fi

# Docker images for the project
@clean_docker_images: clean_docker_containers
    project_images=$(docker images | grep {{ project_slug }} | awk '{print $3}'); \
    if [[ -n $project_images ]]; then \
        docker rmi $project_images; \
    fi

# Remove all docker volumes except the database volume for the project
@clean_docker_volumes: clean_docker_images
    volumes=$(docker volume ls | grep {{ project_slug }} | grep -v postgres_data | awk '{print $2}'); \
    if [[ -n $volumes ]]; then \
        docker volume rm $volumes; \
    fi

# Remove cached Python bytecode
@clean_py_cache:
    rm -r `find . -name '__pycache__' -type d`

# Run Django's collectstatic management command
@collectstatic:
    just _start_msg "Collecting static files"
    {{ python_cmd_prefix }} ./manage.py collectstatic --no-input --no-default-ignore --clear

# First-time setup: bring services up, create the superuser, then attach.
# Run this on first install; use `just start` for every subsequent boot.
@init:
    just install_hooks
    just _start_msg "Initial setup: bringing services up"
    docker compose up --wait -d
    just create_superuser
    just start

# Install Git hooks (pre-commit -> just format, pre-push -> just lint)
@install_hooks:
    just _start_msg "Installing Git hooks"
    git config core.hooksPath .githooks
    chmod +x .githooks/pre-commit .githooks/pre-push

# Dump the database
@db_dump:
    just _start_msg "Dumping the database"
    docker compose up --wait -d db
    docker compose run -v ~/Downloads:/downloads --rm db pg_dump --no-privileges --no-owner --format=custom ${DATABASE_URL} --file=/downloads/{{ project_slug }}-`date +%Y%m%d-%H%M%S`.dump

# Restore the database
db_restore dump_file="":
    #!/usr/bin/env bash
    if test -z "{{dump_file}}"; then
      DUMP_FILE=$(ls ~/Downloads/{{ project_slug }}-* | sort | tail -n 1)
    else
      DUMP_FILE="{{dump_file}}"
    fi
    just _start_msg "Restoring the database "${POSTGRES_DB}" from the latest dump file in ${DUMP_FILE}"
    docker compose up --wait -d db
    docker compose exec -T db psql -h db -U ${POSTGRES_DB} -d postgres -c "DROP DATABASE IF EXISTS ${POSTGRES_DB};" > /dev/null
    docker compose exec -T db psql -h db -U ${POSTGRES_DB} -d postgres -c "CREATE DATABASE ${POSTGRES_DB};" > /dev/null
    docker compose exec -T db pg_restore -d ${DATABASE_URL} --no-owner --no-privileges < "${DUMP_FILE}"

# Serve documentation locally with Zensical (on port 4000)
@docs:
    uv run zensical serve -f zensical.toml

# Build the documentation site (outputs to docs_site/)
@docs-build:
    uv run zensical build -f zensical.toml --clean

# Lint documentation links
@docs-lint: lint_docs

# Format all code
@format: format_py format_js format_just format_html

# Format HTML
@format_html:
    just _start_msg "Formatting HTML using djLint"
    {{ python_cmd_prefix }} djlint . --reformat --quiet

# Format Javascript code
@format_js:
    just _start_msg "Formatting Javascript code using oxfmt + oxlint"
    {{ bun_cmd_prefix }} bun run format-js

# Format the justfile
@format_just:
    just _start_msg "Formatting the justfile"
    just --fmt --unstable

# Format all code natively via uvx/bunx (no Docker); used by the pre-commit hook.
# Tool versions are read from uv.lock / package.json so they match Docker + CI exactly.
format_native:
    #!/usr/bin/env bash
    set -eu
    missing=()
    command -v uvx >/dev/null 2>&1 || missing+=("uv (provides uvx) — https://docs.astral.sh/uv/getting-started/installation/")
    command -v bunx >/dev/null 2>&1 || missing+=("bun (provides bunx) — https://bun.sh/docs/installation")
    if [ "${#missing[@]}" -gt 0 ]; then
        echo "just format_native needs these on your PATH:" >&2
        printf '  - %s\n' "${missing[@]}" >&2
        echo "Install them, or run 'just format' to format via Docker instead." >&2
        exit 1
    fi
    ruff_ver=$(grep -A1 '^name = "ruff"$' uv.lock | grep -m1 '^version = ' | sed -E 's/version = "([^"]+)"/\1/')
    djlint_ver=$(grep -A1 '^name = "djlint"$' uv.lock | grep -m1 '^version = ' | sed -E 's/version = "([^"]+)"/\1/')
    oxfmt_ver=$(grep -m1 '"oxfmt":' package.json | sed -E 's/.*"oxfmt": *"([^"]+)".*/\1/')
    oxlint_ver=$(grep -m1 '"oxlint":' package.json | sed -E 's/.*"oxlint": *"([^"]+)".*/\1/')
    just _start_msg "Formatting Python code using ruff ${ruff_ver}"
    uvx "ruff@${ruff_ver}" format
    uvx "ruff@${ruff_ver}" check --fix
    just _start_msg "Formatting HTML using djLint ${djlint_ver}"
    uvx "djlint@${djlint_ver}" . --reformat --quiet
    just _start_msg "Formatting Javascript code using oxfmt ${oxfmt_ver} + oxlint ${oxlint_ver}"
    bunx "oxfmt@${oxfmt_ver}" ./frontend/
    bunx "oxlint@${oxlint_ver}" --fix ./frontend/
    just _start_msg "Formatting the justfile"
    just --fmt --unstable

# Format Python code
@format_py:
    just _start_msg "Formatting Python code using ruff"
    {{ python_cmd_prefix }} ruff format
    {{ python_cmd_prefix }} ruff check --fix

# Lint everything
lint: lint_js lint_html lint_py lint_migrations lint_types

# Lint docs links
@lint_docs:
    just _start_msg "Check documentation links"
    {{ python_cmd_prefix }} mkdocs-linkcheck ./docs

# Lint HTML
@lint_html:
    just _start_msg "Checking HTML using djLint"
    {{ python_cmd_prefix }} djlint . --lint

# Lint Javascript code with oxfmt + oxlint
@lint_js:
    just _start_msg "Checking Javascript formatting (oxfmt) and code (oxlint)"
    {{ bun_cmd_prefix }} bun run lint-js

# Check for missing Django migrations
@lint_migrations:
    just _start_msg "Check for missing Django migrations"
    {{ python_cmd_prefix_with_deps }} ./manage.py makemigrations --check --dry-run

# Lint Python code ruff
@lint_py:
    just _start_msg "Checking code using Ruff"
    {{ python_cmd_prefix }} ruff check
    {{ python_cmd_prefix }} ruff format --check

# Lint Python types
@lint_types:
    just _start_msg "Checking python types using ty"
    {{ python_cmd_prefix }} ty check .

# Run pre-commit checks
pre_commit: format lint test test_e2e

# Start docker compose
@start:
    docker compose up

# Start docker compose with debugpy
@start_with_debugpy:
    USE_DEBUGPY=true docker compose up

# Start docker compose with full services
@start_full:
    docker compose --profile full up

# Stop all docker-compose services
@stop:
    docker compose down -t 0

# Run tests without coverage
@test:
    {{ python_cmd_prefix }} pytest --ds=config.settings.test_runner

# Run tests with coverage
@test_with_coverage:
    {{ python_cmd_prefix }} pytest --cov --ds=config.settings.test_runner
    {{ python_cmd_prefix }} coverage html && open htmlcov/index.html

# Run Playwright e2e tests against pre-built frontend assets.
@test_e2e *args:
    just _start_msg "Running Playwright e2e tests"
    just build_frontend
    {{ python_cmd_prefix }} pytest e2e/ --ds=config.settings.e2e {{ args }}

# Upgrade frontend (bun) requirements based on `package.json` file
@upgrade_node_packages:
    just _start_msg "Upgrading frontend requirements"
    {{ bun_cmd_prefix }} bun update

# Upgrade python requirements
upgrade_python_packages +packages="":
    #!/usr/bin/env bash
    export VIRTUAL_ENV=/opt/venv
    if [ -z "{{ packages }}" ]; then
        echo "Upgrading all requirements from pyproject.toml...";
        {{ python_cmd_prefix }} $VIRTUAL_ENV/bin/uv sync --all-packages --all-extras;
    else
        echo "Upgrading specified packages: {{ packages }}";
        # First install the package with --upgrade
        {{ python_cmd_prefix }} $VIRTUAL_ENV/bin/uv pip install --upgrade {{ packages }};
        # Then sync to ensure dependencies are consistent
        {{ python_cmd_prefix }} $VIRTUAL_ENV/bin/uv sync --all-extras;
    fi
