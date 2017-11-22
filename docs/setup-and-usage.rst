Setup and Usage Instructions
============================

Setup Instructions
------------------

.. note::

    If you want to use Vagrant then use the :ref:`Vagrant Instructions <using-vagrant>`. Otherwise, continue with these instructions.

Before you begin make sure you've setup and installed `Pipenv <https://docs.pipenv.org/>`_ and `Virtualenvwrapper <https://virtualenvwrapper.readthedocs.io/en/latest/>`_. You can use the Django base site without Virtualenvwrapper however you won't be able to use the ``workon`` command.

Change the directory to where you want keep your django projects.

.. code-block:: bash

    $ cd ~/Sites

In the same directory run the following commands to download the template.

.. code-block:: bash

    $ export PROJECT_NAME=example
    $ curl -LOk https://github.com/epicserve/django-base-site/archive/master.zip && unzip master
    $ mv django-base-site-master $PROJECT_NAME
    $ cd $PROJECT_NAME

Setup your virtualenv with pipenv and install the project requirements.

.. code-block:: bash

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

Remove all unnecessary example configs and template files.

.. code-block:: bash

    $ make clean

Setup your database:

.. code-block:: bash

    $ chmod +x manage.py
    $ ./manage.py migrate

At this point your base site should be setup and you can now run your dev server.

.. code-block:: bash

    $ ./manage.py runserver


Usage
-----

**Running the development server**

After following the `Setup Instructions`_ you can work on your project again by doing the following.

.. code-block:: bash

    $ workon example
    $ ./manage.py runserver


**How to edit and build the SCSS and Javascript source files:**

First from the root of the project install gulp and the node requirements. This requires that your first install `node <https://nodejs.org/en/>`_.

.. code-block:: bash

    $ npm install -g gulp
    $ npm install

Then you can run ``gulp`` which will watch for changes to your SCSS and Javascript files changes in the ``./src`` directory.

.. code-block:: bash

    $ gulp
