help:
	@echo "clean                      Remove all unnecessary files"
	@echo "coverage                   Run tests with coverage and open the coverage report"
	@echo "download_db_from_heroku    Create a Postgres dump on Heroku and download it"
	@echo "fix_py_imports             Update the imports so they pass linting"
	@echo "lint                       Check code with pep8 and pyflakes"
	@echo "lint_docs                  Check docs"
	@echo "remove_coverage_data       Remove coverage data"
	@echo "remove_heroku              Remove heroku specific files"
	@echo "remove_py_cache_files      Remove python cache files"
	@echo "run_sphinx_autobuild       Run Sphinx Autobuild"
	@echo "restore_db                 Restore database from a sql dump"
	@echo "test                       Run tests using coverage"

clean: remove_py_cache_files remove_coverage_data
	-@rm -rf docs/
	-@rm -f README.md
	-@rm -rf config/apache/
	-@rm -rf config/gunicorn/
	-@rm -rf config/nginx/
	-@rm -rf config/upstart/
	-@rm -r start_new_site.sh

coverage:
	@coverage run manage.py test && coverage html && open htmlcov/index.html

download_db_from_heroku:
	- heroku pg:backups:capture
	- heroku pg:backups:download

lint_py:
	@echo "Checking code using flake8 ..."
	@flake8

lint_js:
	@echo "Checking Javascript code using jshint ..."
	@jshint ./src/js/

lint_imports:
	@echo "Checking python imports ..."
	@isort --recursive --check-only --diff .

lint: lint_js lint_py lint_imports

fix_py_imports:
	@isort --recursive .

lint_docs:
	@echo "Check sphinx docs ..."
	@cd docs && sphinx-build -nW -b json -d _build/doctrees . _build/json

remove_coverage_data:
	-@rm -f .coverage
	-@rm -rf htmlcov

remove_heroku:
	-@rm -f Procfile
	-@rm -f config/heroku_wsgi.py
	-@rm -f runtime.txt

remove_py_cache_files:
	-@rm -r `find . -name '__pycache__' -type d`
	-@find . -name "*.pyc" -delete

run_sphinx_autobuild:
	@sphinx-autobuild docs docs/_build/html

restore_db:
	# You'll need the db container up and running with `docker-compose up -d db` before running this task. After this runs
	# you'll have to connect with a DB client like pgAdmin and then rename that random hashed database name to the one
	# you're using in your project.
	- docker-compose exec -T -u postgres db pg_restore --verbose --clean --no-acl --no-owner -C -d postgres < latest.dump

test:
	@./manage.py test
