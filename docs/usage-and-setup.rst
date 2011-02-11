Usage and Setup Instructions
============================

Usage
-----

The Django Base Site contains a skeleton base site that can be used to jumpstart any new Django site. Please feel free to fork this project and adapt it to your own personal taste. To setup a new website just follow the setup instructions bellow.

Setup Instructions
------------------

Before you begin make sure you've setup and installed `Django-environment <http://github.com/epicserve/django-environment>`_.

Create a directory for your new Django site. ::

$ cd Sites/
$ mkdir example
$ cd example/

In the same directory run the following command to setup a virtualenv for your new site.

``$ mkvirtualenv --no-site-packages example``

Answer the questions to setup your Django-environment. ::

    Is this a Django-enviroment your creating (y/n)? [Default: y] y
    Enter the python path to the config directory ... [Default: example.config] config
    Development server address? [Default: 127.0.0.1] <enter>
    Development server address? [Default: 8000] <enter>
    Create a blank Fabric fabfile in your project (y/n)? [Default: y] y

Remove the config directory created by Django-environment because it will be replaced by the Django base site.

``$ rm -rf config/``

Clone the source from the Django Base Site to your `DJANGO_PROJECT_ROOT` which should be your current directory.
              
``$ git clone git://github.com/epicserve/epicserve-ui.git .``

You might want to remove the ``.git`` directory so you can track changes to your new project under a new git repository.

``rm -rf .git``

Install the base requirements and development requirements.

``$ pip install -r config/requirements.txt -r config/dev-requirements.txt``

Setup your database:

``$ django-admin.py syncdb``

At this point your base site should be setup and you can now run your dev server.

``$ runserver``