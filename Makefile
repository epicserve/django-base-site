help:
	@echo "clean                   Remove all unnecessary files"
	@echo "coverage                Run tests with coverage and open the coverage report"
	@echo "lint                    Check code with pep8 and pyflakes"
	@echo "lint_docs               Check docs"
	@echo "remove_coverage_data    Remove coverage data"
	@echo "remove_heroku           Remove heroku specific files"
	@echo "remove_pyc_files        Remove *.pyc files"
	@echo "run_sphinx_autobuild    Run Sphinx Autobuild"
	@echo "test                    Run tests using coverage"

clean: remove_pyc_files remove_coverage_data remove_heroku
	-@rm -f config/create_local_settings_file.py
	-@rm -rf docs/
	-@rm -f readme.rst
	-@rm -rf static/js/site_name/
	-@rm -rf config/apache/
	-@rm -rf config/cron/
	-@rm -rf config/gunicorn/
	-@rm -rf config/nginx/
	-@rm -rf config/upstart/
	-@rm -rf bin/
	-@rm -rf htmlcov/
	-@rm -f .coverage

coverage:
	@coverage run manage.py test && coverage html && open htmlcov/index.html

lint:
	-@echo "Checking code using flakes8 ..."
	-@flake8 . --exclude=env/ --ignore=E501,F403

lint_docs:
	@echo "Check sphinx docs ..."
	@cd docs && sphinx-build -nW -b json -d _build/doctrees . _build/json

remove_coverage_data:
	-@rm -f .coverage
	-@rm -rf htmlcov

remove_heroku:
	-@rm -f Profile
	-@rm -f config/heroku_wsgi.py
	-@rm -f config/requirements/heroku.txt
	-@rm -f config/settings/heroku.py
	-@rm -f requirements.txt
	-@rm -f runtime.txt

remove_pyc_files:
	-@find . -name "*.pyc" -delete

run_sphinx_autobuild:
	@sphinx-autobuild docs docs/_build/html

test:
	@./manage.py test
