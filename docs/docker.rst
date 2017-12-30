
.. _using-docker:

Using Docker
============

If you want to try out the ``django-base-site`` using Docker then you first
need to `install docker <https://docs.docker.com/engine/installation/>`_. Then
you can go through the following steps.

1. First download the ``django-base-site`` wherever you want your new project.

::

    $ TARGET_DIR=~/Sites/ BRANCH=master PROJECT_NAME=example
    $ cd $TARGET_DIR
    $ curl -L "https://github.com/epicserve/django-base-site/archive/$BRANCH.zip" | tar zx -C $TARGET_DIR && mv "django-base-site-$BRANCH" $PROJECT_NAME
    $ cd $PROJECT_NAME

2. Create your ``.env`` file.

::

    $ export SECRET_KEY=$(python -c "import random; print(''.join(random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789%^&*(-_=+)') for i in range(50)))")
    $ cat > .env <<EOF
    DEBUG=on
    DATABASE_URL=postgres://postgres@db:5432/postgres
    SECRET_KEY='$SECRET_KEY'
    EMAIL_HOST='smtp.planetspaceball.com'
    EMAIL_HOST_USER='skroob@planetspaceball.com'
    EMAIL_HOST_PASSWORD='12345'
    DEFAULT_FROM_EMAIL="President Skroob <skroob@planetspaceball.com>"
    ALLOWED_HOSTS=*
    INTERNAL_IPS=192.168.99.100,127.0.0.1,0.0.0.0,localhost,172.18.0.1
    CACHE_URL=rediscache://127.0.0.1:6379/1?client_class=django_redis.client.DefaultClient
    EOF

3. Build your service images.

::

    $ docker-compose build

4. Create a super user.

::

    $ docker-compose run web python manage.py createsuperuser

5. Run the Django runserver.

::

    $ docker-compose up


Debugging
---------

ipdb
~~~~

Set a trace like you normally do in your code and then go to that view in your browser and then stop ``docker-compose up``.

::

    import ipdb; ipdb.set_trace()

Then you can run the following to work interactive debugging shell.

::

    docker-compose run --service-ports web

PyCharm
~~~~~~~

- Follow `Jetbrain's guide <https://www.jetbrains.com/help/pycharm/using-docker-compose-as-a-remote-interpreter.html>`_.
- Make sure you pull up the site using http://localhost:8000/ instead of http://127.0.0.1:8000/.
- You'll also need to add 172.18.0.1 to your INTERNAL_IPS.


Running Gulp
------------

You can run gulp by simply running the, ``docker-compose run web gulp`` command.
To stop gulp watch, you would normally hit ``CTL+C``, however that doesn't seem
to work so you'll have to run ``docker-compose ps`` to get the container name,
then run something like ``docker kill djangobasesite_web_run_1`` to stop gulp watch.


Common Gotchas
--------------
- You need to start your runserver using `docker-compose up` instead of
  `docker-compose run web python manage.py runserver 0.0.0.0:8000` or you
  won't be able to access your site from your browser.
- Installing `django-debug-toolbar` can ignore the Django version you've
  specified in your `Pipfile` and instead Django 2 because django-debug-toolbar
  uses "Django" with a capital D in it's requirements when other packages use
  "django" in lowercase. To work around this install everything except
  `django-debug-toolbar` and then added it last to your `Pipfile`.
- If you get a message like, "ERROR: The Docker Engine version is less than the
  minimum required by Compose. Your current project requires a Docker Engine of
  version 1.13.0 or greater." You can run `docker-machine upgrade` to upgrade
  your version of `docker-compose`.


Common Commands
---------------

===================  ==================================================================================================
Command              Description
===================  ==================================================================================================
docker-compose up    Starts up all of your services according to how they were defined in your docker-compose.yml file.
docker-compose down  Stops containers and removes containers, networks, volumes, and images created by `up`.
docker volume ls     List the volumes that have been created
===================  ==================================================================================================


References
----------
- `A Brief Intro to Docker for Djangonauts <https://www.revsys.com/tidbits/brief-intro-docker-djangonauts/>`_
