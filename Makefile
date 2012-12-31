

clean:
	-./utils/create_local_settings_file.py
	-rm create_local_settings_file.py
	-rm -rf docs/
	-rm readme.rst
	-rm -rf static/js/site_name/
	-rm -rf config/apache/
	-rm -rf config/cron/
	-rm -rf config/gunicorn/
	-rm -rf config/nginx/
	-rm -rf config/upstart/
	-rm -rf bin/
	-rm Makefile