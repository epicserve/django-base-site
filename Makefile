help:
	-@echo "clean                   Remove all unnecessary files"
	-@echo "remove_pyc_files        Remove *.pyc files"
	-@echo "remove_coverage_data    Remove coverage data"
	-@echo "check_code_style        Check code with pep8 and pyflakes"
	-@echo "test                    Run tests using coverage"
	-@echo "test_report             Open the coverage report"


clean: remove_pyc_files remove_coverage_data remove_heroku
	-@rm -f utils/create_local_settings_file.py
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

remove_heroku:
	-@rm -f Profile
	-@rm -f config/heroku_wsgi.py
	-@rm -f config/requirements/heroku.txt
	-@rm -f config/settings/heroku.py

remove_pyc_files:
	-@find . -name "*.pyc" -delete

remove_coverage_data:
	-@rm -f .coverage
	-@rm -rf htmlcov

check_code_style:
	-@echo "Checking code using pep8 ..."
	-@pep8 --ignore E501 .
	-@echo "Checking code using pyflakes ..."
	-@pyflakes .

test:
	-coverage run --source='.' manage.py test

test_report:
	-coverage html && open htmlcov/index.html
