Django Base Site
================

The Django Base Site is a skeleton base site that can be used to jumpstart any
new Django site. [Brent O'Connor](http://twitter.com/epicserve/) created it so
he could use it personally to jumpstart any of his new Django projects. Please
feel free to fork this project and adapt it to your own personal taste.


Documentation
-------------

Documentation is available at [http://django-base-site.readthedocs.org/](http://django-base-site.readthedocs.org/).

Features
--------

- [Bootstrap 4](https://getbootstrap.com/)
- [Coverage](https://bitbucket.org/ned/coveragepy)
- [Django 2](https://www.djangoproject.com/)
- [Django Compressor](https://github.com/django-compressor/django-compressor)
- [Django Debug Toolbar](https://github.com/django-compressor/django-compressor)
- [Django-allauth](http://www.intenct.nl/projects/django-allauth/)
- [Django-environ](https://django-environ.readthedocs.io/en/latest/) for [12factor](https://www.12factor.net/) inspired environment variables
- [Gulp](https://gulpjs.com/) for building SASS and JS with [Browserify](http://browserify.org/) for requiring modules and [Babel](https://babeljs.io/) for transpiling ES6/ES2015.
- [Pipenv](https://github.com/kennethreitz/pipenv)
- [Vagrant Support](https://www.vagrantup.com/)
- [Docker Support](https://www.docker.com/)
- Sample configs for [Apache](https://github.com/epicserve/django-base-site/tree/master/config/apache), [Gunicorn](https://github.com/epicserve/django-base-site/tree/master/config/gunicorn), [Nginx](https://github.com/epicserve/django-base-site/tree/master/config/nginx) and [Upstart](https://github.com/epicserve/django-base-site/tree/master/config/upstart)

Install Requirements
--------------------

Before setting up a new project make sure you have the following installed:

* Python 3.5 or newer 
* [Pipenv](https://github.com/kennethreitz/pipenv)
* [virtualenv](https://github.com/pypa/virtualenv)

It's not a requirement, but it is recommended that you install Python using [Pyenv](https://github.com/pyenv/pyenv) with the [virtualenvwrapper](https://github.com/pyenv/pyenv-virtualenvwrapper) plugin. 


One-liner Quickstart
--------------------

Running the following script does the same thing as quickstart guide.

    $ bash <(curl -s https://raw.githubusercontent.com/epicserve/django-base-site/master/start_new_site.sh)


Quickstart
----------

    $ curl -LOk https://github.com/epicserve/django-base-site/archive/master.zip && unzip master
    $ mv django-base-site-master example
    $ cd example
    $ pipenv install --dev --python $(which python3)
    $ export SECRET_KEY=$(python -c "import random; print(''.join(random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789%^&*(-_=+)') for i in range(50)))")
    $ cat > .env <<EOF
    DEBUG=on
    SECRET_KEY='$SECRET_KEY'
    EMAIL_HOST='smtp.planetspaceball.com'
    EMAIL_HOST_USER='skroob@planetspaceball.com'
    EMAIL_HOST_PASSWORD='12345'
    DEFAULT_FROM_EMAIL="President Skroob <skroob@planetspaceball.com>"
    EOF
    $ pipenv shell
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
    $ heroku addons:create rediscloud
    $ heroku buildpacks:add --index 1 heroku/nodejs
    $ heroku config
    $ heroku config:set READ_DOT_ENV_FILE=off \
    WSGI_APPLICATION=config.heroku_wsgi.application \
    SECRET_KEY='random string of 50 chars' \
    DEFAULT_FROM_EMAIL='$MAILGUN_SMTP_LOGIN' \
    EMAIL_HOST='$MAILGUN_SMTP_SERVER' \
    EMAIL_HOST_USER='$MAILGUN_SMTP_LOGIN' \
    EMAIL_HOST_PASSWORD='$MAILGUN_SMTP_PASSWORD' \
    ALLOWED_HOSTS='*'
    $ git push --set-upstream heroku master
    $ heroku run python manage.py migrate
    $ heroku run python manage.py createsuperuser    
    $ heroku open

**Note:**
Before you'll be able to send email using Mailgun you'll have to setup
your Heroku app on a custom domain under Heroku and Mailgun.
