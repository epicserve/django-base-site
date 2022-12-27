# Django Base Site

![CI](https://github.com/epicserve/django-base-site/actions/workflows/ci.yml/badge.svg)
[![Documentation Status](https://readthedocs.org/projects/django-base-site/badge/?version=latest)](https://django-base-site.readthedocs.io/en/latest/?badge=latest)

<!--intro-start-->
The Django Base Site is a Django site that is built using the best Django practices and comes with all the common Django
packages that you need to jumpstart your next project.
<!--intro-end-->

## Documentation

Documentation is available at [http://django-base-site.readthedocs.org/](http://django-base-site.readthedocs.org/).

<!--readme-start-->
## Features

* [Black](https://black.readthedocs.io/en/stable/) for automatic Python code formatting
* [Bootstrap 5](https://getbootstrap.com/)
* [Celery](http://docs.celeryproject.org/)
* [Custom User Model](https://docs.djangoproject.com/en/stable/topics/auth/customizing/#substituting-a-custom-user-model)
* [Django 4.1](https://www.djangoproject.com/)
* [Django Crispy Forms](https://github.com/django-crispy-forms/django-crispy-forms)
* [Django Debug Toolbar](https://github.com/jazzband/django-debug-toolbar)
* [Django-allauth](http://www.intenct.nl/projects/django-allauth/)
* [Docker Support](https://www.docker.com/)
* [Environs](https://github.com/sloria/environs) for [12factor](https://www.12factor.net/) inspired environment variables
* [Eslint](https://eslint.org/) for linting Javascript
* [Just](https://github.com/casey/just) for running common commands (make equivalent)
* [MkDocs](https://www.mkdocs.org/) for documentation
* [Mypy](http://mypy-lang.org/) for Python Type checking
* [Pip-tools](https://github.com/jazzband/pip-tools/)
* [Pytest Django](https://pytest-django.readthedocs.io/en/latest/index.html)
* [Pytest-cov](https://pytest-cov.readthedocs.io)
* [Pytest](https://docs.pytest.org/)
* [Ruff](https://github.com/charliermarsh/ruff) for extra Python linting
* [Stylelint](https://stylelint.io/) for linting SASS
* [Vite](https://vitejs.dev/) for building SASS and JS
* [dj Lint](https://djlint.com/) for formatting and linting HTML

## Install Requirements

Installing locally with Python is possible but not supported. The preferred way is to use the quickstart script below
and to use Docker with docker-compose. Before proceeding make sure you've
[installed Docker](https://docs.docker.com/engine/installation/). For running common commands install
[Just](https://github.com/casey/just). Once installed you can run `just` to see the list of commands available.


## Quickstart

### Using the Install Script

Running the following script mostly does the same thing as manual quickstart method. The exception is that the install
script has questions to customize your new project setup. Just run the following in your terminal to get started.

**Note:** When start the Django runserver it will take several seconds before the CSS styles take effect. This is
because Vite is running in dev mode which takes a few seconds to take effect.
    
```bash
bash <(curl -s https://raw.githubusercontent.com/epicserve/django-base-site/main/scripts/start_new_project)
```
    
Example output:

    $ cd ~/Sites
    $ bash <(curl -s https://raw.githubusercontent.com/epicserve/django-base-site/main/scripts/start_new_project)
    
    What is the project name slug [example]?
    What directory do you want your project in [/Users/brento/Sites/example]?
    Are going to use Docker Compose (Y/n)? Y

    Done.

    To start Docker Compose run:
    $ cd /Users/brento/Sites/example
    $ just start

### Manual

    $ curl -LOk https://github.com/epicserve/django-base-site/archive/main.zip && unzip main
    $ mv django-base-site-main example
    $ cd example
    $ mkdir -p public/static
    $ export SECRET_KEY=$(python -c "import random; print(''.join(random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789%^&*(-_=+)') for i in range(50)))")
    $ cat > .env <<EOF
    DEBUG=on
    SECRET_KEY='$SECRET_KEY'
    EOF
    $ just start


## Deploy to Fly.io

1. [Install flyctl](https://fly.io/docs/hands-on/install-flyctl/)
2. Run `fly launch`. Make sure you add the Postgres and Redis services. Example:
   ```
   $ fly launch
   Update available 0.0.437 -> 0.0.441.
   Run "fly version update" to upgrade.
   Creating app in /Users/brento/Sites/personal/django-base-site
   Scanning source code
   Detected a NodeJS app
   Using the following build configuration:
           Builder: heroku/buildpacks:20
   ? Choose an app name (leave blank to generate one): django-base-site
   automatically selected personal organization: Brent O'Connor
   ? Choose a region for deployment: Denver, Colorado (US) (den)
   Created app django-base-site in organization personal
   Admin URL: https://fly.io/apps/django-base-site
   Hostname: django-base-site.fly.dev
   Wrote config file fly.toml
   ? Would you like to set up a Postgresql database now? Yes
   ? Select configuration: Development - Single node, 1x shared CPU, 256MB RAM, 1GB disk
   Creating postgres cluster in organization personal
   Creating app...
   Setting secrets on app django-base-site-db...
   Provisioning 1 of 1 machines with image flyio/postgres:14.4
   Waiting for machine to start...
   Machine 59185000a14d83 is created
   ==> Monitoring health checks
     Waiting for 59185000a14d83 to become healthy (started, 3/3)
   
   Postgres cluster django-base-site-db created
     Username:    postgres
     Password:    <redacted>
     Hostname:    django-base-site-db.internal
     Proxy port:  5432
     Postgres port:  5433
     Connection string: postgres://postgres:<redacted>@django-base-site-db.internal:5432
   
   Save your credentials in a secure place -- you won't be able to see them again!
   
   Connect to postgres
   Any app within the Brent O'Connor organization can connect to this Postgres using the following connection string:
   
   Now that you've set up Postgres, here's what you need to understand: https://fly.io/docs/postgres/getting-started/what-you-should-know/
   
   Postgres cluster django-base-site-db is now attached to django-base-site
   The following secret was added to django-base-site:
     DATABASE_URL=postgres://django_base_site:<redacted>@top2.nearest.of.django-base-site-db.internal:5432/django_base_site?sslmode=disable
   Postgres cluster django-base-site-db is now attached to django-base-site
   ? Would you like to set up an Upstash Redis database now? Yes
   ? Select an Upstash Redis plan Free: 100 MB Max Data Size
   input:3: createAddOn Validation failed: Name has already been taken
   
   ? Would you like to deploy now? No
   Your app is ready! Deploy with `flyctl deploy`
   ```
3. Edit the `fly.toml` file udate the following sections so they match below. Also make sure you replace `<app_name>`
   The name of the app that was created when you ran `fly launch`.
   ```
   [build]
     dockerfile = "config/docker/Dockerfile"

   [build.args]
     ENV_NAME = "prod"

   [deploy]
     release_command = "python manage.py migrate --noinput"

   [env]
     PORT = "8080"
     ALLOWED_HOSTS = "<app_name>.fly.dev"
     INTERNAL_IPS = "<app_name>.fly.dev"
     DB_SSL_REQUIRED = "off"
   ```
4. Set secret environment variables:
   ```
   fly secrets set SECRET_KEY=$(python -c "import random; print(''.join(random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789%^&*(-_=+)') for i in range(50)))")
   ```
5. Run `fly deploy` to deploy your app to Fly.io
6. Run `fly ssh console` and run `cd /srv/app && ./manage.py createsuperuser` to create your user for signing in.
7. Run `fly open` to open the app in your browser. You won't be able to login via /accounts/login/ until you validate
   your email address. To do this go to /admin/ and sign in. Then go to /admin/account/emailaddress/ and mark your email
   address as primary and validated. Then you should be able to sign in with the normal sign in view. If you had
   your app setup to send email then you wouldn't have to validate your email address in the admin first because when
   you sign in, the app would send you an email with a link to click on to validate your email address.
8. If you end up getting a 500 error and need to debug it, you can add the following to your settings and then run
   `fly deploy`. Once the app is deployed, you can trigger the 500 error again and then when you run `fly logs`, you
   should be able to see a python traceback of the exception error.

## Contribute

1. Look for an open [issue](https://github.com/epicserve/django-base-site/issues) or create new issue to get a dialog going about the new feature or bug that you've discovered.
2. Fork the [repository](https://github.com/epicserve/django-base-site) on GitHub to start making your changes to the master branch (or branch off of it). 
3. Make a pull request.

<!--readme-end-->
