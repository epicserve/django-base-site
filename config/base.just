# This is base Just file that is used to keep all common commands across projects.
#
# Documentation: https://github.com/casey/just
# Use docker compose as the default prefix for commands. Set these environment variables to an empty string to overwrite
# running with docker-compose.

python_cmd_prefix := env_var_or_default('PYTHON_CMD_PREFIX', 'docker compose run --no-deps --rm web')
python_cmd_prefix_with_deps := env_var_or_default('PYTHON_CMD_PREFIX_WITH_DEPS', 'docker compose run --rm web')
node_cmd_prefix := env_var_or_default('NODE_CMD_PREFIX', 'docker compose run --no-deps --rm -e NODE_ENV=production node')

set dotenv-load := true

# COLORS

green := `tput -Txterm setaf 2`
reset := `tput -Txterm sgr0`

@_green message:
    echo "{{ green }}{{ message }}{{ reset }}"

@_start_msg msg:
    just _green "{{ msg }} ..."

# Build Docker images
@build:
    just _start_msg "Building docker project"
    docker volume rm {{ project_slug }}_node_modules
    docker compose build
    just collectstatic

# Build frontend assets
@build_frontend:
    {{ node_cmd_prefix }} npm run build
    just collectstatic

# Remove build files, python cache files and test coverage data
@clean: clean_py_cache clean_coverage_data
    rm -rf .mypy_cache/
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

# Format all code
@format: format_py format_js format_just format_sass format_html

# Format HTML
@format_html:
    just _start_msg "Formatting HTML using djLint"
    {{ python_cmd_prefix }} djlint . --reformat --quiet

# Format Javascript code
@format_js:
    just _start_msg "Formatting Javascript code using eslint"
    {{ node_cmd_prefix }} npm run format-js

# Format the justfile
@format_just:
    just _start_msg "Formatting the justfile"
    just --fmt --unstable

# Format Python code
@format_py:
    just _start_msg "Formatting Python code using black"
    {{ python_cmd_prefix }} ruff format
    {{ python_cmd_prefix }} ruff check --fix

# Format SASS/CSS code
@format_sass:
    just _start_msg "Formatting SASS code using stylelint"
    {{ node_cmd_prefix }} npm run format-sass

# Lint everything
lint: lint_js lint_sass lint_html lint_py lint_migrations lint_types

# Lint docs with mkdocs-linkcheck
@lint_docs:
    just _start_msg "Check mkdocs docs using mkdocs-linkcheck"
    {{ python_cmd_prefix }} mkdocs-linkcheck ./docs

# Lint HTML
@lint_html:
    just _start_msg "Checking HTML using djLint"
    {{ python_cmd_prefix }} djlint . --lint

# Lint Javascript code with eslint
@lint_js:
    just _start_msg "Checking Javascript code using eslint"
    {{ node_cmd_prefix }} npm run lint-js

# Check for missing Django migrations
@lint_migrations:
    just _start_msg "Check for missing Django migrations"
    {{ python_cmd_prefix_with_deps }} ./manage.py makemigrations --check --dry-run

# Lint Python code ruff
@lint_py:
    just _start_msg "Checking code using Ruff"
    {{ python_cmd_prefix }} ruff check
    {{ python_cmd_prefix }} ruff format --check

# Lint SASS code with stylelint
@lint_sass:
    just _start_msg "Checking SASS code using stylelint"
    {{ node_cmd_prefix }} npm run lint-sass

# Lint Python types
@lint_types:
    just _start_msg "Checking python types using mypy"
    {{ python_cmd_prefix }} mypy .

# Run pre-commit checks
pre_commit: format lint test

# Start docker compose
@start:
    docker compose up

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

# Upgrade node requirements based on `package.json` file
@upgrade_node_packages:
    just _start_msg "Upgrading node requirements"
    {{ node_cmd_prefix }} npm upgrade

# Upgrade python requirements
@upgrade_python_packages +packages="":
    if [ -z "{{ packages }}" ]; then \
        echo "Upgrading all requirements based on .in files..."; \
        rm -rf ./config/requirements/*.txt; \
        {{ python_cmd_prefix }} uv pip compile --upgrade --generate-hashes --output-file config/requirements/prod_lock.txt config/requirements/prod.in; \
        {{ python_cmd_prefix }} uv pip compile --upgrade --generate-hashes --output-file config/requirements/dev_lock.txt config/requirements/dev.in; \
    else \
        echo "Upgrading specified packages: {{ packages }}"; \
        package_args=`python -c "print(' '.join([f'--upgrade-package {package}' for package in '{{ packages }}'.split(' ')]))"`; \
        {{ python_cmd_prefix }} uv pip compile $package_args --generate-hashes --output-file config/requirements/prod_lock.txt config/requirements/prod.in; \
        {{ python_cmd_prefix }} uv pip compile $package_args --generate-hashes --output-file config/requirements/dev_lock.txt config/requirements/dev.in; \
    fi
