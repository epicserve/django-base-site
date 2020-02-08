Django Base Site
================

The Django Base Site is a Django site that is built using the best Django practices and comes with all the common Django
packages that you need to jumpstart your next project.


Documentation
-------------

Documentation is available at [http://django-base-site.readthedocs.org/](http://django-base-site.readthedocs.org/).

Features
--------

- [Black](https://black.readthedocs.io/en/stable/) for automatic Python code formatting
- [Bootstrap 4](https://getbootstrap.com/)
- [Celery](http://docs.celeryproject.org/)
- [Coverage](https://bitbucket.org/ned/coveragepy)
- [Custom User Model](https://docs.djangoproject.com/en/2.1/topics/auth/customizing/#substituting-a-custom-user-model)
- [Django 3](https://www.djangoproject.com/)
- [Django Crispy Forms](https://github.com/django-crispy-forms/django-crispy-forms)
- [Django Debug Toolbar](https://github.com/jazzband/django-debug-toolbar)
- [Django REST framework](https://www.django-rest-framework.org/)
- [Django-allauth](http://www.intenct.nl/projects/django-allauth/)
- [Docker Support](https://www.docker.com/)
- [Eslint](https://eslint.org/) for linting Javascript
- [Environs](https://github.com/sloria/environs) for [12factor](https://www.12factor.net/) inspired environment variables
- [Mypy](http://mypy-lang.org/) for Python Type checking
- [Pipenv](https://github.com/kennethreitz/pipenv)
- [Stylelint](https://stylelint.io/) for linting SASS
- [Vagrant Support](https://www.vagrantup.com/)
- [Webpack](https://webpack.js.org/) for building SASS and JS with [Babel](https://babeljs.io/)
- Sample configs for [Apache](https://github.com/epicserve/django-base-site/tree/master/config/apache), [Gunicorn](https://github.com/epicserve/django-base-site/tree/master/config/gunicorn), [Nginx](https://github.com/epicserve/django-base-site/tree/master/config/nginx) and [Upstart](https://github.com/epicserve/django-base-site/tree/master/config/upstart)

Install Requirements
--------------------

Before setting up a new project make sure you have the following installed:

* Python 3.5 or newer 
* [Pipenv](https://github.com/kennethreitz/pipenv)
* [virtualenv](https://github.com/pypa/virtualenv)

It's not a requirement, but it is recommended that you install Python using [Pyenv](https://github.com/pyenv/pyenv) with the [virtualenvwrapper](https://github.com/pyenv/pyenv-virtualenvwrapper) plugin. 


Quickstart
----------

### Using the Install Script

Running the following script mostly does the same thing as manual quickstart method. The exception is that the install
script has questions to customize your new project setup. Just run the following in your terminal to get started.

    $ bash <(curl -s https://raw.githubusercontent.com/epicserve/django-base-site/master/start_new_site.sh)
    
Example output:

    $ cd ~/Sites
    $ bash <(curl -s https://raw.githubusercontent.com/epicserve/django-base-site/master/start_new_site.sh)
    
    What is the project name slug [example]?
    What directory do you want your project in [/Users/brento/Sites/example]?
    Are going to use Docker Compose (Y/n)? Y
    Are going to Heroku for deployment (Y/n)? Y

    Done.

    To start Docker Compose run:
    $ cd /Users/brento/Sites/example
    $ docker-compose up

### Manual

    $ curl -LOk https://github.com/epicserve/django-base-site/archive/master.zip && unzip master
    $ mv django-base-site-master example
    $ cd example
    $ pipenv install --dev --python $(which python3)
    $ export SECRET_KEY=$(python -c "import random; print(''.join(random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789%^&*(-_=+)') for i in range(50)))")
    $ cat > .env <<EOF
    DEBUG=on
    SECRET_KEY='$SECRET_KEY'
    EMAIL_URL='smtp://username:password@smtp.example.com:587/?ssl=True&_default_from_email=John%20Example%20%3Cjohn%40example.com%3E'
    # Uncomment the following if you're using docker-compose
    # DATABASE_URL=postgres://postgres@db:5432/postgres
    CACHE_URL=redis://redis:6379/0
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
    $ heroku buildpacks:add --index 2 heroku/python
    $ alias hg='heroku config:get'
    $ heroku config:set READ_DOT_ENV_FILE=off \
    WSGI_APPLICATION=config.heroku_wsgi.application \
    SECRET_KEY=`python -c "import random; print(''.join(random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789%^&*(-_=+)') for i in range(50)))"` \
    EMAIL_URL=smtp://`hg MAILGUN_SMTP_LOGIN`:`hg MAILGUN_SMTP_PASSWORD`@`hg MAILGUN_SMTP_SERVER`:`hg MAILGUN_SMTP_PORT`'/?ssl=True&_default_from_email='`hg MAILGUN_SMTP_LOGIN` \
    ALLOWED_HOSTS='*' \
    CACHE_URL=`hg REDISCLOUD_URL`
    $ git push --set-upstream heroku master
    $ heroku run python manage.py migrate
    $ heroku run python manage.py createsuperuser    
    $ heroku open

**Note:**
Before you'll be able to send email using Mailgun you'll have to setup
your Heroku app on a custom domain under Heroku and Mailgun.
