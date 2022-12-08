# This is just file that uses just to run commands.
# Documentation: https://github.com/casey/just


# Use docker-compose as the default prefix for commands. Set these environment variables to an empty string to overwrite
# running with docker-compose.
python_cmd_prefix := env_var_or_default('PYTHON_CMD_PREFIX', 'docker-compose run --no-deps --rm web')
python_cmd_prefix_with_deps := env_var_or_default('PYTHON_CMD_PREFIX_WITH_DEPS', 'docker-compose run --rm web')
node_cmd_prefix := env_var_or_default('NODE_CMD_PREFIX', 'docker-compose run --no-deps --rm -e NODE_ENV=production node')


# COLORS
green  := `tput -Txterm setaf 2`
reset  := `tput -Txterm sgr0`


# List available commands
default:
  @just -l

_green message:
    @echo "{{green}}{{message}}{{reset}}"

_start_msg msg:
  @just _green "{{msg}} ..."

# Remove build files, python cache files and test coverage data
clean: remove_py_cache remove_coverage_data 
  @rm -rf docs/_build/
  @rm -rf public/static/
  @rm -rf .mypy_cache

# Format SASS/CSS code
format_css:
  @just _start_msg "Formatting SASS/CS code using stylelint"
  @{{node_cmd_prefix}} npm run format-sass

# Format HTML
format_html:
  @just _start_msg "Formatting HTML using djLint"
  @{{python_cmd_prefix}} djlint . --reformat

# Format Javascript code
format_js:
  @just _start_msg "Formatting Javascript code using eslint"
  @{{node_cmd_prefix}} npm run format-js

# Format Python code
format_py:
  @just _start_msg "Formatting Python code using black"
  @{{python_cmd_prefix}} black .

# Format Python imports with isort
format_py_imports:
  @just _start_msg "Formatting Python imports using isort"
  @{{python_cmd_prefix}} isort .

# Format all code
format: format_py_imports format_py format_js format_css format_html

# Lint Python code flake8
lint_py:
  @just _start_msg "Checking code using black and flake8"
  @{{python_cmd_prefix}} black . --check
  @# Just use x until the issue https://github.com/PyCQA/flake8/issues/234 is resolved and we can configure in pyproject.toml
  @{{python_cmd_prefix}} flake8 --ignore=E501 .
  @echo ""

# Lint Javascript code with eslint
lint_js:
  @just _start_msg "Checking Javascript code using eslint"
  @{{node_cmd_prefix}} npx eslint ./src/js/
  @echo ""

# Lint Python imports with isort
lint_imports:
  @just _start_msg "Checking python imports using isort"
  @{{python_cmd_prefix}} isort --check-only --diff .
  @echo ""

# Check for missing Django migrations
lint_migrations:
  @just _start_msg "Check for missing Django migrations"
  @{{python_cmd_prefix_with_deps}} ./manage.py makemigrations --check --dry-run
  @echo ""

# Lint SASS code with stylelint
lint_sass:
  @just _start_msg "Checking SASS code using stylelint"
  @{{node_cmd_prefix}} npx stylelint ./src/scss/
  @echo ""

# Lint HTML
lint_html:
  @just _start_msg "Checking HTML using djLint"
  @{{python_cmd_prefix}} djlint . --lint
  @echo ""

# Lint Python types
lint_types:
  @just _start_msg "Checking python types using mypy"
  @{{python_cmd_prefix}} mypy .
  @echo ""

# Lint docs with mkdocs-linkcheck
lint_docs:
  @just _start_msg "Check mkdocs docs using mkdocs-linkcheck"
  @{{python_cmd_prefix}} mkdocs-linkcheck
  @echo ""

# Lint everything
lint: lint_js lint_sass lint_html lint_py lint_imports lint_migrations lint_types

# Run pip-compile make the requirement files
make_requirements:
  @rm -rf ./requirements*.txt
  @{{python_cmd_prefix}} pip-compile --upgrade --generate-hashes --output-file requirements.txt config/requirements/prod.in
  @{{python_cmd_prefix}} pip-compile --upgrade --generate-hashes --output-file requirements-dev.txt config/requirements/dev.in

# Run the django test runner with coverage
open_coverage:
  @{{python_cmd_prefix}} coverage html && open htmlcov/index.html

# Remove Django test coverage data
remove_coverage_data:
  @rm -f .coverage
  @rm -rf htmlcov

# Remove extra Django Base Site files not needed in a new project
remove_extra_files:
  @rm -f LICENSE.md
  @rm -f README.md
  @rm -r scripts/start_new_project

# Remove cached Python bytecode
remove_py_cache:
  @rm -r `find . -name '__pycache__' -type d`

# Start all docker-compose services
start:
  @docker-compose up

# Stop all docker-compose services
stop:
  @docker-compose down -t 0

# Run the Django test runner without coverage
test:
  @{{python_cmd_prefix}} pytest --cov
