Setup and Usage Instructions
============================

Setup Instructions
------------------

.. note::

    If you want to use Docker then use the :ref:`Docker Instructions <using-docker>`. Otherwise, continue with these instructions.

Change the directory to where you want keep your django projects.

.. code-block:: bash

    $ cd ~/Sites

In the same directory run the following commands to download the template.

.. code-block:: bash

    $ export PROJECT_NAME=example
    $ curl -LOk https://github.com/epicserve/django-base-site/archive/master.zip && unzip master
    $ mv django-base-site-master $PROJECT_NAME
    $ cd $PROJECT_NAME
    $ mkdir -p public/static

Setup your virtualenv and install the project requirements.

.. code-block:: bash

    $ python -m venv .venv && source .venv/bin/activate
    $ pip install --upgrade pip-tools
    # Install from the source requirements because iPython hashes are created in Docker and the install fails under
    # Mac OS because there are no hashes created for iPython's requirement of appnope when using darwin.
    $ pip install --upgrade --requirement ./config/requirements/dev.in
    $ export SECRET_KEY=$(python -c "import random; print(''.join(random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789%^&*(-_=+)') for i in range(50)))")
    $ cat > .env <<EOF
    DEBUG=on
    SECRET_KEY='$SECRET_KEY'
    EMAIL_URL='smtp://username:password@smtp.example.com:587/?ssl=True&_default_from_email=John%20Example%20%3Cjohn%40example.com%3E'
    EOF

Remove all unnecessary example configs and template files.

.. code-block:: bash

    $ make clean

Setup your database:

.. code-block:: bash

    $ chmod +x manage.py
    $ ./manage.py migrate

At this point your base site should be installed and you can now run your dev server. However, CSS and Javascript won't load until you run `npm run build` or `npm run watch`.

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

First from the root of the project install webpack and the node requirements. This requires that your first install `node <https://nodejs.org/en/>`_.

.. code-block:: bash

    $ npm install

Then you can run ``webpack`` which will watch for changes to your SCSS and Javascript files changes in the ``./src`` directory.

.. code-block:: bash

    $ npm run watch
