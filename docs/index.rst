Django Base Site
================

Contents
--------

.. toctree::
   :maxdepth: 1

   setup-and-usage
   docker
   s3
   website-launch-checklist

About
-----

The Django Base Site is a Django site that is built using the best Django practices and comes with all the common Django
packages that you need to jumpstart your next project.

Install Requirements
--------------------

Before setting up a new project make sure you have the following installed:

* Python 3.5 or newer
* `Pip-tools <https://github.com/jazzband/pip-tools/>`_
* `virtualenv <https://github.com/pypa/virtualenv>`_

It's not a requirement, but it is recommended that you install Python using `Pyenv <https://github.com/pyenv/pyenv>`_ with the `virtualenvwrapper <https://github.com/pyenv/pyenv-virtualenvwrapper>`_ plugin.

Features
--------

- `Black <https://black.readthedocs.io/en/stable/>`_ for automatic Python code formatting
- `Bootstrap 4 <https://getbootstrap.com/>`_
- `Celery <http://docs.celeryproject.org/>`_
- `Coverage <https://bitbucket.org/ned/coveragepy>`_
- `Custom User Model <https://docs.djangoproject.com/en/stable/topics/auth/customizing/#substituting-a-custom-user-model>`_
- `Django 3 <https://www.djangoproject.com/>`_
- `Django Crispy Forms <https://github.com/django-crispy-forms/django-crispy-forms>`_
- `Django Debug Toolbar <https://github.com/jazzband/django-debug-toolbar>`_
- `Django REST framework <https://www.django-rest-framework.org/>`_
- `Django-allauth <http://www.intenct.nl/projects/django-allauth/>`_
- `Docker Support <https://www.docker.com/>`_
- `Eslint <https://eslint.org/>`_ for linting Javascript
- `Environs <https://github.com/sloria/environs>`_ for `12factor <https://www.12factor.net/>`_ inspired environment variables
- `Mypy <http://mypy-lang.org/>`_ for Python Type checking
- `Pip-tools <https://github.com/jazzband/pip-tools/>`_
- `Stylelint <https://stylelint.io/>`_ for linting SASS
- `Webpack <https://webpack.js.org/>`_ for building SASS and JS with `Babel <https://babeljs.io/>`_
- Sample configs for `Apache <https://github.com/epicserve/django-base-site/tree/master/config/apache>`_, `Gunicorn <https://github.com/epicserve/django-base-site/tree/master/config/gunicorn>`_, `Nginx <https://github.com/epicserve/django-base-site/tree/master/config/nginx>`_ and `Upstart <https://github.com/epicserve/django-base-site/tree/master/config/upstart>`_

Contribute
----------

#. Look for an open `issue <https://github.com/epicserve/django-base-site/issues>`_ or create new issue to get a dialog going about the new feature or bug that you've discovered.

#. Fork the `repository <https://github.com/epicserve/django-base-site>`_ on Github to start making your changes to the master branch (or branch off of it).

#. Make a pull request.
