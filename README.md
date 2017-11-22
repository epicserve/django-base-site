Django Base Site
================

The Django Base Site is a skeleton base site that can be used to jumpstart any
new Django site. [Brent O'Connor](http://twitter.com/epicserve/) created it so
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
    $ heroku config:set DJANGO_SETTINGS_MODULE=config.settings
    $ heroku config:set WSGI_APPLICATION=config.heroku_wsgi.application
    $ heroku config:set SECRET_KEY='random string of 50 chars'
    $ heroku config:set DEFAULT_FROM_EMAIL='$MAILGUN_SMTP_LOGIN'
    $ heroku config:set EMAIL_HOST='$MAILGUN_SMTP_SERVER'
    $ heroku config:set EMAIL_HOST_USER='$MAILGUN_SMTP_LOGIN'
    $ heroku config:set EMAIL_HOST_PASSWORD='$MAILGUN_SMTP_PASSWORD'
    $ heroku config:set ALLOWED_HOSTS='*'
    $ git push --set-upstream heroku master
    $ heroku run python manage.py migrate
    $ heroku run python manage.py createsuperuser
    $ heroku open

**Note:**
Before you'll be able to send email using Mailgun you'll have to setup
your Heroku app on a custom domain under Heroku and Mailgun.
