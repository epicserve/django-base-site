Django Base Site
================

Contents
--------

.. toctree::
   :maxdepth: 1

   setup-and-usage
   vagrant
   docker
   pre-commit-hook
   website-launch-checklist

About
-----

The Django Base Site is a skeleton base site that can be used to jumpstart any
new Django site. `Brent O'Connor <http://twitter.com/epicserve/>`_ created it so
he could use it personally to jumpstart any of his new Django projects. Please
feel free to fork this project and adapt it to your own personal taste. To
setup a new website just follow the :doc:`setup-and-usage`.

Install Requirements
--------------------

Before setting up a new project make sure you have the following installed:

* Python 3.5 or newer
* `Pipenv <https://github.com/kennethreitz/pipenv>`_
* `virtualenv <https://github.com/pypa/virtualenv>`_

It's not a requirement, but it is recommended that you install Python using `Pyenv <https://github.com/pyenv/pyenv>`_ with the `virtualenvwrapper <https://github.com/pyenv/pyenv-virtualenvwrapper>`_ plugin.

Features
--------

- `Bootstrap 4 <https://getbootstrap.com/>`_
- `Coverage <https://bitbucket.org/ned/coveragepy>`_
- `Django 2 <https://www.djangoproject.com/>`_
- `Django Compressor <https://github.com/django-compressor/django-compressor>`_
- `Django Debug Toolbar <https://github.com/django-compressor/django-compressor>`_
- `Django-allauth <http://www.intenct.nl/projects/django-allauth/>`_
- `Django-environ <https://django-environ.readthedocs.io/en/latest/>`_ for `12factor <https://www.12factor.net/>`_ inspired environment variables
- `Gulp <https://gulpjs.com/>`_ for building SASS and JS with `Browserify <http://browserify.org/>`_ for requiring modules and `Babel <https://babeljs.io/>`_ for transpiling ES6/ES2015.
- `Pipenv <https://github.com/kennethreitz/pipenv>`_
- `Vagrant Support <https://www.vagrantup.com/>`_
- Sample configs for `Apache <https://github.com/epicserve/django-base-site/tree/master/config/apache>`_, `Gunicorn <https://github.com/epicserve/django-base-site/tree/master/config/gunicorn>`_, `Nginx <https://github.com/epicserve/django-base-site/tree/master/config/nginx>`_ and `Upstart <https://github.com/epicserve/django-base-site/tree/master/config/upstart>`_

Contribute
----------

#. Look for an open `issue <https://github.com/epicserve/django-base-site/issues>`_ or create new issue to get a dialog going about the new feature or bug that you've discovered.

#. Fork the `repository <https://github.com/epicserve/django-base-site>`_ on Github to start making your changes to the master branch (or branch off of it).

#. Make a pull request.
