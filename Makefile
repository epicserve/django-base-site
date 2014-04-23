help:
	-@echo "clean    Remove all unessary files"

clean:
	-mv config/settings/local.py.example config/settings/local.py
	-rm -rf docs/
	-rm readme.rst
	-rm .gitignore
	-rm -rf static/js/site_name/
	-rm -rf config/apache/
	-rm -rf config/cron/
	-rm -rf config/gunicorn/
	-rm -rf config/nginx/
	-rm -rf config/upstart/
	-rm -rf bin/
