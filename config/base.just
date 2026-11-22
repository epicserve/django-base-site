# This is base Just file that is used to keep all common commands across projects.
#
# Documentation: https://github.com/casey/just
# Use docker compose as the default prefix for commands. Set these environment variables to an empty string to overwrite
# running with docker-compose.

python_cmd_prefix := env_var_or_default('PYTHON_CMD_PREFIX', 'docker compose exec web')
python_cmd_prefix_with_deps := env_var_or_default('PYTHON_CMD_PREFIX_WITH_DEPS', 'docker compose exec web')
bun_cmd_prefix := env_var_or_default('BUN_CMD_PREFIX', 'docker compose run --no-deps --rm -e NODE_ENV=production frontend')

# Native (uvx/bunx) tool versions, read from the lockfiles so they match Docker + CI
ruff_version := `grep -A1 '^name = "ruff"$' uv.lock | grep -m1 '^version = ' | sed -E 's/version = "([^"]+)"/\1/'`
djlint_version := `grep -A1 '^name = "djlint"$' uv.lock | grep -m1 '^version = ' | sed -E 's/version = "([^"]+)"/\1/'`
oxfmt_version := `grep -m1 '"oxfmt":' package.json | sed -E 's/.*"oxfmt": *"([^"]+)".*/\1/'`
oxlint_version := `grep -m1 '"oxlint":' package.json | sed -E 's/.*"oxlint": *"([^"]+)".*/\1/'`

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

# Ensure uvx + bunx (the native format/lint runners) are on PATH
_require_native_tools:
    #!/usr/bin/env bash
    set -eu
    missing=()
    command -v uvx >/dev/null 2>&1 || missing+=("uv (provides uvx) — https://docs.astral.sh/uv/getting-started/installation/")
    command -v bunx >/dev/null 2>&1 || missing+=("bun (provides bunx) — https://bun.sh/docs/installation")
    if [ "${#missing[@]}" -gt 0 ]; then
        echo "Native format/lint needs these on your PATH:" >&2
        printf '  - %s\n' "${missing[@]}" >&2
        exit 1
    fi

# vue-tsc and openapi-typescript need the project's node_modules. With the default Docker prefix they run in the
# frontend container, which has them; natively (BUN_CMD_PREFIX="", as in CI) they need a local `bun install`.
_require_node_modules:
    #!/usr/bin/env bash
    if [ -n "{{ bun_cmd_prefix }}" ]; then
        exit 0
    fi
    if [ ! -x node_modules/.bin/vue-tsc ] || [ ! -d node_modules/openapi-typescript ]; then
        echo "node_modules is missing or out of date; run \`bun install\` first." >&2
        exit 1
    fi

# Build Docker images
@build:
    just _start_msg "Building docker project"
    # Remove the frontend container, running or not, so the node_modules volume can go; the new image refills it
    docker compose rm --stop --force frontend
    docker volume rm --force "$(just _compose_project)_node_modules"
    docker compose build
    # A one-off container from the new image: `exec web` would need web running, and would use the old image
    PYTHON_CMD_PREFIX="docker compose run --rm --no-deps -T web" just collectstatic

# Build frontend assets
@build_frontend:
    {{ bun_cmd_prefix }} bun run build
    just collectstatic

# Remove build files, python cache files and test coverage data
@clean: clean_py_cache clean_coverage_data
    rm -rf .ty_cache/
    rm -rf .pytest_cache/
    rm -rf .ruff_cache/
    rm -rf .cache/
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
    volumes=$(docker volume ls -q --filter "label=com.docker.compose.project=$(just _compose_project)" | grep -v '_postgres_data$'); \
    if [ -n "$volumes" ]; then \
        docker volume rm $volumes; \
    fi

# This checkout's Compose project: COMPOSE_PROJECT_NAME from .env (a worktree's own, see scripts/worktree), else the
# directory name. Name and find volumes by it, not by project_slug, which is only the main checkout's.
@_compose_project:
    docker compose config | sed -n 's/^name: //p'

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

# Install Git hooks (pre-commit -> just format, pre-push -> just lint). Skips with a note when this
# directory isn't the root of a Git repository yet (e.g. a new project that hasn't been `git init`-ed).
install_hooks:
    #!/usr/bin/env bash
    set -e
    if [ ! -e .git ]; then
        if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
            echo "Skipping Git hooks: this directory is inside the Git repository at $(git rev-parse --show-toplevel) but isn't its root, so a relative core.hooksPath would point at the wrong place."
        else
            echo "Skipping Git hooks: this directory isn't a Git repository yet. Run 'git init' and then 'just install_hooks' to enable them."
        fi
        exit 0
    fi
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

# Format all code natively via uvx/bunx (no Docker); versions come from uv.lock / package.json
@format: _require_native_tools
    just _start_msg "Formatting Python code using ruff {{ ruff_version }}"
    uvx "ruff@{{ ruff_version }}" format
    uvx "ruff@{{ ruff_version }}" check --fix
    just _start_msg "Formatting HTML using djLint {{ djlint_version }}"
    uvx "djlint@{{ djlint_version }}" . --reformat --quiet
    just _start_msg "Formatting Javascript using oxfmt {{ oxfmt_version }} + oxlint {{ oxlint_version }}"
    bunx "oxfmt@{{ oxfmt_version }}" ./frontend/
    bunx "oxlint@{{ oxlint_version }}" --fix ./frontend/
    just _start_msg "Formatting the justfile"
    just --fmt --unstable

# Regenerate the SPA's API types in frontend/js/api/ from the ninja and allauth OpenAPI specs
@generate_api_types: _require_native_tools _require_node_modules _ensure_web
    just _start_msg "Generating API types in frontend/js/api/"
    just _generate_api_types frontend/js/api

# Export both OpenAPI specs and write their TypeScript types to `out_dir`. The specs go under .cache/ in the repo,
# which the web and frontend containers both mount, so this works with the Docker prefixes too.
_generate_api_types out_dir:
    #!/usr/bin/env bash
    set -euo pipefail
    spec_dir=.cache/api-types/specs
    mkdir -p "$spec_dir" "{{ out_dir }}"
    {{ python_cmd_prefix_with_deps }} ./manage.py export_openapi_schema --settings=config.settings.api_types \
        --api config.api.api --sorted --indent 2 --output "$spec_dir/api.json"
    {{ python_cmd_prefix_with_deps }} ./manage.py export_allauth_openapi_schema --settings=config.settings.api_types \
        --output "$spec_dir/allauth.json"
    {{ bun_cmd_prefix }} bun frontend/config/generate-api-types.mjs "$spec_dir/api.json" "{{ out_dir }}/schema.d.ts"
    {{ bun_cmd_prefix }} bun frontend/config/generate-api-types.mjs "$spec_dir/allauth.json" "{{ out_dir }}/allauth.d.ts"

# Lint everything
lint: lint_js lint_html lint_py lint_migrations lint_deploy lint_types lint_api_types lint_ts

# Fail if the checked-in API types in frontend/js/api/ don't match the backend's schemas
lint_api_types: _require_native_tools _require_node_modules
    #!/usr/bin/env bash
    set -euo pipefail
    just _start_msg "Checking the API types in frontend/js/api/ match the backend"
    check_dir=.cache/api-types/check
    rm -rf "$check_dir"
    just _generate_api_types "$check_dir"
    if ! diff -r -q frontend/js/api "$check_dir" >/dev/null; then
        diff -r -u frontend/js/api "$check_dir" | head -n 40 || true
        echo "The API types in frontend/js/api/ are stale. Run \`just generate_api_types\` and commit the result." >&2
        exit 1
    fi

# Run Django's deployment checks (`check --deploy`) against the production defaults: DEBUG off, no .env, and none of
# the HTTPS settings overridden. The secret key is a placeholder long enough to pass the check; nothing is signed with it.
@lint_deploy:
    just _start_msg "Running Django's deployment checks"
    {{ python_cmd_prefix_with_deps }} env -u SECURE_SSL_REDIRECT -u SECURE_HSTS_SECONDS -u SECURE_HSTS_INCLUDE_SUBDOMAINS \
        -u SECURE_HSTS_PRELOAD -u SESSION_COOKIE_SECURE -u CSRF_COOKIE_SECURE \
        READ_DOT_ENV_FILE=off DEBUG=off ALLOWED_HOSTS=example.com \
        SECRET_KEY=placeholder-for-the-deployment-checks-never-used-to-sign-anything \
        ./manage.py check --deploy --fail-level WARNING --settings=config.settings.deploy_check

# Lint HTML
@lint_html: _require_native_tools
    just _start_msg "Checking HTML using djLint {{ djlint_version }}"
    uvx "djlint@{{ djlint_version }}" . --lint

# Lint Javascript code with oxfmt + oxlint
@lint_js: _require_native_tools
    just _start_msg "Checking Javascript using oxfmt {{ oxfmt_version }} + oxlint {{ oxlint_version }}"
    bunx "oxfmt@{{ oxfmt_version }}" --check ./frontend/
    bunx "oxlint@{{ oxlint_version }}" ./frontend/

# Check for missing Django migrations (needs the project deps, so runs via Docker locally)
@lint_migrations:
    just _start_msg "Check for missing Django migrations"
    {{ python_cmd_prefix_with_deps }} ./manage.py makemigrations --check --dry-run

# Lint Python code ruff
@lint_py: _require_native_tools
    just _start_msg "Checking code using ruff {{ ruff_version }}"
    uvx "ruff@{{ ruff_version }}" check
    uvx "ruff@{{ ruff_version }}" format --check

# Type-check the SPA's TypeScript and Vue files with vue-tsc
@lint_ts: _require_native_tools _require_node_modules
    just _start_msg "Checking TypeScript using vue-tsc"
    {{ bun_cmd_prefix }} node_modules/.bin/vue-tsc --noEmit -p frontend/tsconfig.json

# Lint Python types
@lint_types:
    just _start_msg "Checking python types using ty"
    {{ python_cmd_prefix }} ty check .

# Run pre-commit checks
pre_commit: format lint test test_js test_e2e

# Lint, then run pytest stopping at the first failure (last run's failures first). One after the other, not in
# parallel, so the output reads top to bottom. Run it before calling work done.
@verify: _ensure_web lint
    just _start_msg "Running tests"
    {{ python_cmd_prefix }} pytest --ds=config.settings.test_runner -x --ff -q

# Create known dev logins, organizations, teams and invites (DEBUG only; safe to rerun)
@seed: _ensure_web
    just _start_msg "Seeding development data"
    {{ python_cmd_prefix }} ./manage.py seed

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

# Run the SPA's unit tests (`frontend/js/**/*.test.ts`) with bun's built-in test runner
@test_js:
    just _start_msg "Running the SPA's unit tests with bun test"
    {{ bun_cmd_prefix }} bun test ./frontend/js/

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

# Upgrade Python packages in uv.lock: all of them, or only the ones named (the next `just build` installs them)
upgrade_python_packages +packages="":
    #!/usr/bin/env bash
    set -euo pipefail
    if [ -z "{{ packages }}" ]; then
        echo "Upgrading all Python packages in uv.lock..."
        upgrade=(--upgrade)
    else
        echo "Upgrading in uv.lock: {{ packages }}"
        upgrade=()
        for package in {{ packages }}; do upgrade+=(--upgrade-package "$package"); done
    fi
    # A one-off web container, so this works whether or not the stack is up. It runs as your user with HOME=/ and a
    # root-owned /opt/venv, so uv gets a writable cache and only updates uv.lock; `just build` rebuilds the venv.
    docker compose run --rm --no-deps -T -e UV_CACHE_DIR=/tmp/uv-cache web /opt/venv/bin/uv lock "${upgrade[@]}"
