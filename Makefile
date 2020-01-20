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
PYTHON_CMD_PREFIX_WITH_WEB_PORT ?= docker-compose run -p 8000:8000 --no-deps --rm web
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

.PHONY: coverage
coverage: ## Run the django test runner with coverage
	@$(PYTHON_CMD_PREFIX) coverage run manage.py test && $(PYTHON_CMD_PREFIX) coverage html && open htmlcov/index.html

.PHONY: download_db_from_heroku
download_db_dump: ## Download a dump of your heroku Postgres DB
	@heroku pg:backups:capture
	@heroku pg:backups:download

.PHONY: fix_py_imports
fix_py_imports: ## Fix Python imports with isort
	@$(PYTHON_CMD_PREFIX) isort --recursive .

.PHONY: lint_py
lint_py: ## Lint Python code flake8
	@echo "Checking code using flake8 ..."
	@$(PYTHON_CMD_PREFIX) flake8

.PHONY: lint_js
lint_js: ## Lint Javascript code with eslint
	@echo "Checking Javascript code using eslint ..."
	@$(NODE_CMD_PREFIX) npx eslint ./src/js/

.PHONY: lint_imports
lint_imports: ## Lint Python imports with isort
	@echo "Checking python imports ..."
	@$(PYTHON_CMD_PREFIX) isort --recursive --check-only --diff .

.PHONY: lint_sass
lint_sass: ## Lint SASS code with stylelint
	@echo "Checking SASS code using stylelint ..."
	@$(NODE_CMD_PREFIX) npx stylelint ./src/scss/

.PHONY: lint_types
lint_types: ## Lint Python types
	@echo "Checking python types ..."
	@$(PYTHON_CMD_PREFIX) mypy .

.PHONY: lint_docs
lint_docs: ## Lint docs with Sphinx
	@echo "Check sphinx docs ..."
	@$(PYTHON_CMD_PREFIX) sphinx-build -nW -b json -d ./docs/_build/doctrees ./docs ./docs/_build/json

.PHONY: lint
lint: lint_js lint_sass lint_py lint_imports lint_types ## Lint Javascript, SASS, Python, Python imports and Python types

.PHONY: remove_coverage_data
remove_coverage_data: ## Remove Django test coverage data 
	@rm -f .coverage
	@rm -rf htmlcov

.PHONY: remove_docker_compose
remove_docker_compose: ## Remove Docker Compose related files
	@rm -f Dockerfile
	@rm -f Dockerfile.node
	@rm -f docker-compose.yml

.PHONY: remove_extra_files
remove_extra_files: ## Remove extra Django Base Site files not needed in a new project
	@rm -rf docs/
	@rm -f LICENSE.md
	@rm -f README.md
	@rm -rf config/apache/
	@rm -rf config/gunicorn/
	@rm -rf config/nginx/
	@rm -rf config/upstart/
	@rm -r start_new_site.sh

.PHONY: remove_heroku
remove_heroku: ## Remove files used for Heroku
	@rm -f Procfile

.PHONY: remove_py_cache
remove_py_cache: ## Remove cached Python bytecode
	@rm -r `find . -name '__pycache__' -type d`

.PHONY: remove_vagrant
remove_vagrant: ## Remove files related to Vagrant
	@rm -f Vagrantfile
	@rm -rf config/vagrant

.PHONY: restore_db
restore_db: download_db_dump ## Download DB dump from heroku and reload it into your docker compose DB
	# You'll need the db container up and running with `docker-compose up -d db` before running this task. After this runs
	# you'll have to connect with a DB client like pgAdmin and then rename that random hashed database name to the one
	# you're using in your project.
	@docker-compose exec -T -u postgres db pg_restore --verbose --clean --no-acl --no-owner -C -d postgres < latest.dump

.PHONY: sphinx_autobuild
sphinx_autobuild: ## Run sphinx autobuild
	@$(PYTHON_CMD_PREFIX_WITH_WEB_PORT) sphinx-autobuild --host 0.0.0.0 ./docs ./docs/_build/html

.PHONY: test
test: ## Run the Django test runner without coverage
	@$(PYTHON_CMD_PREFIX) ./manage.py test --parallel
