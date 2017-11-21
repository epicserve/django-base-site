Django Base Site
================

The Django Base Site is a skeleton base site that can be used to jumpstart any
new Django site. `Brent O'Connor <http://twitter.com/epicserve/>`_ created it so
he could use it personally to jumpstart any of his new Django projects. Please
feel free to fork this project and adapt it to your own personal taste.


Documentation
-------------

Documentation is available at [http://django-base-site.readthedocs.org/](http://django-base-site.readthedocs.org/).


Quickstart
----------

    $ curl -LOk https://github.com/epicserve/django-base-site/archive/master.zip && unzip master
    $ mv django-base-site-master example
    $ cd example
    $ virtualenv --python=python3 env
    $ source env/bin/activate
    $ pip install -r config/requirements/dev.txt
    $ ./manage.py migrate
    $ ./manage.py createsuperuser
    $ ./manage.py runserver


Deploy on Heroku
----------------

    $ git init
    $ git add .
    $ git commit
    $ heroku create
    $ heroku addons:create mailgun
    $ heroku buildpacks:set https://github.com/heroku/heroku-buildpack-python
    $ heroku config:set DJANGO_SETTINGS_MODULE=config.settings.heroku
    $ heroku config:set SECRET_KEY='random string of 50 chars'
    $ git push --set-upstream heroku master
    $ heroku run python manage.py migrate
    $ heroku run python manage.py createsuperuser
    $ heroku open

Add a site:

**Note:** The admin static assets won't show up until you deploy to Heroku a second time. Not sure why.

* Go to /admin/sites/site/add/
* Add your site
