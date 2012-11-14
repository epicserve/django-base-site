Usage and Setup Instructions
============================

Usage
-----

The Django Base Site contains a skeleton base site that can be used to jumpstart any new Django site. Please feel free to fork this project and adapt it to your own personal taste. To setup a new website just follow the setup instructions bellow.

Setup Instructions
------------------

Before you begin make sure you've setup and installed `Virtualenvwrapper <http://www.doughellmann.com/projects/virtualenvwrapper/>`_.

Create a directory for your new Django site. ::

$ mkdir ~/Sites/example
$ cd ~/Sites/example

In the same directory run the following command to setup a virtualenv for your new site. ::

$ mkvirtualenv --no-site-packages --distribute example

Clone the source from the Django Base Site to your `DJANGO_PROJECT_ROOT` which should be your current directory. ::

$ git clone git://github.com/epicserve/django-base-site.git .

You might want to remove the ``.git`` directory so you can track changes to your new project under a new git repository. ::

$ rm -rf .git

Install the base requirements and development requirements. ::

$ pip install -r config/requirements/dev.txt

Add the to your `DJANGO_PROJECT_ROOT` to your Python path. ::

$ add2virtualenv .

Set your ``DJANGO_SETTINGS_MODULE`` environment variable (You'll need to do this everytime you work on this project). ::

$ export DJANGO_SETTINGS_MODULE=config.settings.development

Setup your database::

$ django-admin.py syncdb

At this point your base site should be setup and you can now run your dev server. ::

$ django-admin.py runserver