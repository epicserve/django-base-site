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
- [Custom User Model](https://docs.djangoproject.com/en/stable/topics/auth/customizing/#substituting-a-custom-user-model)
- [Django 3](https://www.djangoproject.com/)
- [Django Crispy Forms](https://github.com/django-crispy-forms/django-crispy-forms)
- [Django Debug Toolbar](https://github.com/jazzband/django-debug-toolbar)
- [Django REST framework](https://www.django-rest-framework.org/)
- [Django-allauth](http://www.intenct.nl/projects/django-allauth/)
- [Docker Support](https://www.docker.com/)
- [Eslint](https://eslint.org/) for linting Javascript
- [Environs](https://github.com/sloria/environs) for [12factor](https://www.12factor.net/) inspired environment variables
- [Mypy](http://mypy-lang.org/) for Python Type checking
- [Pip-tools](https://github.com/jazzband/pip-tools/)
- [Stylelint](https://stylelint.io/) for linting SASS
- [Webpack](https://webpack.js.org/) for building SASS and JS with [Babel](https://babeljs.io/)
- Sample configs for [Apache](https://github.com/epicserve/django-base-site/tree/main/config/apache), [Gunicorn](https://github.com/epicserve/django-base-site/tree/main/config/gunicorn), [Nginx](https://github.com/epicserve/django-base-site/tree/main/config/nginx) and [Upstart](https://github.com/epicserve/django-base-site/tree/main/config/upstart)

Install Requirements
--------------------

Before setting up a new project make sure you have the following installed:

* Python 3.5 or newer 
* [Pip-tools](https://github.com/jazzband/pip-tools/)
* [virtualenv](https://github.com/pypa/virtualenv)

It's not a requirement, but it is recommended that you install Python using [Pyenv](https://github.com/pyenv/pyenv) with the [virtualenvwrapper](https://github.com/pyenv/pyenv-virtualenvwrapper) plugin. 


Quickstart
----------

### Using the Install Script

Running the following script mostly does the same thing as manual quickstart method. The exception is that the install
script has questions to customize your new project setup. Just run the following in your terminal to get started.

    $ bash <(curl -s https://raw.githubusercontent.com/epicserve/django-base-site/main/scripts/start_new_project)
    
Example output:

    $ cd ~/Sites
    $ bash <(curl -s https://raw.githubusercontent.com/epicserve/django-base-site/main/scripts/start_new_project)
    
    What is the project name slug [example]?
    What directory do you want your project in [/Users/brento/Sites/example]?
    Are going to use Docker Compose (Y/n)? Y

    Done.

    To start Docker Compose run:
    $ cd /Users/brento/Sites/example
    $ docker-compose up

### Manual

    $ curl -LOk https://github.com/epicserve/django-base-site/archive/main.zip && unzip main
    $ mv django-base-site-main example
    $ cd example
    $ python -m venv .venv && source .venv/bin/activate
    $ pip install -r ./requirements-dev.txt
    $ export SECRET_KEY=$(python -c "import random; print(''.join(random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789%^&*(-_=+)') for i in range(50)))")
    $ cat > .env <<EOF
    DEBUG=on
    SECRET_KEY='$SECRET_KEY'
    EMAIL_URL='smtp://username:password@smtp.example.com:587/?ssl=True&_default_from_email=John%20Example%20%3Cjohn%40example.com%3E'
    # Uncomment the following if you're using docker-compose
    # DATABASE_URL=postgres://postgres@db:5432/postgres
    CACHE_URL=redis://redis:6379/0
    EOF
    $ ./manage.py migrate
    $ ./manage.py createsuperuser
    $ ./manage.py runserver
