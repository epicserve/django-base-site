Django Base Site
================

The Django Base Site is a skeleton base site that can be used to jumpstart any
new Django site. `Brent O'Connor <http://twitter.com/epicserve/>`_ created it so
he could use it personally to jumpstart any of his new Django projects. Please
feel free to fork this project and adapt it to your own personal taste.

Documentation
=============

Documentation is available at http://django-base-site.readthedocs.org/.

Quickstart
==========

::

$ curl -LOk https://github.com/epicserve/django-base-site/archive/master.zip && unzip master
$ mv django-base-site-master example
$ cd example
$ virtualenv --python=python3 env
$ source env/bin/activate
$ pip install -r config/requirements/dev.txt
$ ./manage.py migrate
$ ./manage.py createsuperuser
$ ./manage.py runserver
