

clean:
	-python utils/create_local_settings_file.py
	-rm utils/create_local_settings_file.py
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
	-rm Makefile
