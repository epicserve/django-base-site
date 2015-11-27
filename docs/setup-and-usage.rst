Setup and Usage Instructions
============================

Setup Instructions
------------------

.. note::

    If you want to use Vagrant then use the :ref:`Vagrant Instructions <using-vagrant>`. Otherwise, continue with these instructions.

Before you begin make sure you've setup and installed `Virtualenvwrapper <http://www.doughellmann.com/projects/virtualenvwrapper/>`_.

Change the directory to where you want keep your django projects. ::

$ cd ~/Sites

In the same directory run the following command to setup a virtualenv for your new site. ::

$ BRANCH=master PROJECT_NAME=example
$ mkvirtualenv --no-site-packages --distribute $PROJECT_NAME
$ pip install django

Create your Django Base Site. The following will create a new project called "$PROJECT_NAME". ::

$ django-admin.py startproject $PROJECT_NAME --template=https://github.com/epicserve/django-base-site/archive/$BRANCH.zip

Install the base requirements and development requirements. ::

$ cd $PROJECT_NAME
$ pip install -r config/requirements/dev.txt

Setup your python virtual environment to load environment variables and switch you to the project root. ::

$ echo `pwd` > $VIRTUAL_ENV/.project
$ echo 'cdproject' >> $VIRTUAL_ENV/bin/postactivate

Remove all unnecessary example config and template files and create a `config/settings/local.py` settings file::

$ python config/create_local_settings_file.py
$ make clean

Setup your database::

$ chmod +x manage.py
$ ./manage.py migrate

At this point your base site should be setup and you can now run your dev server. ::

$ ./manage.py runserver


Usage
-----

**Running the development server**

After following the `Setup Instructions`_ you can work on your project again by doing the following. ::

$ workon example
$ ./manage.py runserver


**Editing the SCSS/CSS**

First from the root of the project install gulp and the node requirements. This requires that your first install `node <https://nodejs.org/en/>`_. ::

$ npm install -g gulp
$ npm install

Then you can run ``gulp`` which will watch for changes to your SCSS files (e.g. ``static/scss/base.scss``). ::

$ gulp
