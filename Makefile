# For more information on the following see http://clarkgrubb.com/makefile-style-guide
MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help
.DELETE_ON_ERROR:
.SUFFIXES:

# Use docker-compose as the default set these environment variables to an empty
# string to overwrite running with docker-compose.
PYTHON_CMD_PREFIX ?= docker-compose run --no-deps --rm web
PYTHON_CMD_PREFIX_WITH_DEPS ?= docker-compose run --rm web
NODE_CMD_PREFIX ?= docker-compose run --no-deps --rm -e NODE_ENV=production node
HELP_FIRST_COL_LENGTH := 23

# COLORS
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
WHITE  := $(shell tput -Txterm setaf 7)
RESET  := $(shell tput -Txterm sgr0)
TARGET_MAX_CHAR_NUM := 23

.PHONY: help
help:
	@echo ''
	@echo 'Usage:'
	@echo '  ${YELLOW}make${RESET} ${GREEN}<target>${RESET}'
	@echo ''
	@echo 'Targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-$(TARGET_MAX_CHAR_NUM)s$(RESET)$(GREEN)%s$(RESET)\n", $$1, $$2}'
	@echo ''

.PHONY: clean
clean: remove_py_cache remove_coverage_data ## Remove build files, python cache files and test coverage data
	@rm -rf docs/_build/
	@rm -rf public/static/
	@rm -rf .mypy_cache

.PHONY: format_css
format_css: ## Format SASS/CSS code
	@echo "${GREEN}Formatting SASS/CS code using stylelint ...${RESET}"
	@$(NODE_CMD_PREFIX) npm run format-sass

.PHONY: format_html
format_html: ## Format HTML
	@echo "${GREEN}Formatting HTML using djLint ...${RESET}"
	@$(PYTHON_CMD_PREFIX) djlint . --reformat

.PHONY: format_js
format_js: ## Format Javascript code
	@echo "${GREEN}Formatting Javascript code using eslint ...${RESET}"
	@$(NODE_CMD_PREFIX) npm run format-js

.PHONY: format_py
format_py: ## Format Python code
	@echo "${GREEN}Formatting Python code using black ...${RESET}"
	@$(PYTHON_CMD_PREFIX) black .

.PHONY: format_py_imports
format_py_imports: ## Format Python imports with isort
	@echo "${GREEN}Formatting Python imports using isort ...${RESET}"
	@$(PYTHON_CMD_PREFIX) isort .

.PHONY: format_code
format_code: format_py_imports format_py format_js format_css format_html ## Format code

.PHONY: lint_py
lint_py: ## Lint Python code flake8
	@echo "${GREEN}Checking code using black and flake8 ...${RESET}"
	@$(PYTHON_CMD_PREFIX) black . --check
# Just use x until the issue https://github.com/PyCQA/flake8/issues/234 is resolved and we can configure in pyproject.toml
	@$(PYTHON_CMD_PREFIX) flake8 --ignore=E501 .
	@echo ""

.PHONY: lint_js
lint_js: ## Lint Javascript code with eslint
	@echo "${GREEN}Checking Javascript code using eslint ...${RESET}"
	@$(NODE_CMD_PREFIX) npx eslint ./src/js/
	@echo ""

.PHONY: lint_imports
lint_imports: ## Lint Python imports with isort
	@echo "${GREEN}Checking python imports using isort ...${RESET}"
	@$(PYTHON_CMD_PREFIX) isort --check-only --diff .
	@echo ""

.PHONY: lint_migrations
lint_migrations:  ## Check for missing Django migrations
	@echo "${GREEN}Check for missing Django migrations ...${RESET}"
	@$(PYTHON_CMD_PREFIX_WITH_DEPS) ./manage.py makemigrations --check --dry-run
	@echo ""

.PHONY: lint_sass
lint_sass: ## Lint SASS code with stylelint
	@echo "${GREEN}Checking SASS code using stylelint ...${RESET}"
	@$(NODE_CMD_PREFIX) npx stylelint ./src/scss/
	@echo ""

.PHONY: lint_html
lint_html: ## Lint HTML
	@echo "${GREEN}Checking HTML using djLint ...${RESET}"
	@$(PYTHON_CMD_PREFIX) djlint . --lint
	@echo ""

.PHONY: lint_types
lint_types: ## Lint Python types
	@echo "${GREEN}Checking python types using mypy ...${RESET}"
	@$(PYTHON_CMD_PREFIX) mypy .
	@echo ""

.PHONY: lint_docs
lint_docs: ## Lint docs with mkdocs-linkcheck
	@echo "${GREEN}Check mkdocs docs using mkdocs-linkcheck ...${RESET}"
	@$(PYTHON_CMD_PREFIX) mkdocs-linkcheck
	@echo ""

.PHONY: lint
lint: lint_js lint_sass lint_html lint_py lint_imports lint_migrations lint_types ## Lint Javascript, SASS, Python, Python imports and Python types

.PHONY: open_coverage
open_coverage: ## Run the django test runner with coverage
	@$(PYTHON_CMD_PREFIX) coverage html && open htmlcov/index.html

.PHONY: remove_coverage_data
remove_coverage_data: ## Remove Django test coverage data
	@rm -f .coverage
	@rm -rf htmlcov

.PHONY: remove_extra_files
remove_extra_files: ## Remove extra Django Base Site files not needed in a new project
	@rm -f LICENSE.md
	@rm -f README.md
	@rm -r scripts/start_new_project

.PHONY: remove_py_cache
remove_py_cache: ## Remove cached Python bytecode
	@rm -r `find . -name '__pycache__' -type d`

.PHONY: requirements
requirements: ## Run pip-compile to compile the requirements into the requirements*.txt files
	@rm -rf ./requirements*.txt
	@$(PYTHON_CMD_PREFIX) pip-compile --upgrade --generate-hashes --output-file requirements.txt config/requirements/prod.in
	@$(PYTHON_CMD_PREFIX) pip-compile --upgrade --generate-hashes --output-file requirements-dev.txt config/requirements/dev.in

.PHONY: test
test: ## Run the Django test runner without coverage
	@$(PYTHON_CMD_PREFIX) pytest --cov
