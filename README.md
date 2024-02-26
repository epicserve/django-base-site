<h1 align="center">Django Base Site</h1>
<p align="center">
  <a href="https://github.com/epicserve/django-base-site/actions/workflows/ci.yml">
    <img src="https://github.com/epicserve/django-base-site/actions/workflows/ci.yml/badge.svg?branch=main&event=push" alt="CI">
  </a>
  <a href="https://django-base-site.readthedocs.io/en/latest/?badge=latest">
    <img src="https://readthedocs.org/projects/django-base-site/badge/?version=latest" alt="Documentation Status">
  </a>
  <a href="https://github.com/epicserve/django-base-site/blob/main/LICENSE.md">
    <img src="https://img.shields.io/github/license/epicserve/django-base-site.svg" alt="license">
  </a>
</p>

**Documentation**: [django-base-site.readthedocs.org](http://django-base-site.readthedocs.org/)  
**Source Code**: [github.com/epicserve/django-base-site](https://github.com/epicserve/django-base-site/)

---

<!--intro-start-->
The Django Base Site is an opinionated starter template to jump-start any new Django project. It has been lovingly
maintained for over twelve years and has been used to jump-start many other projects. Because it is organized logically,
it will help you and your team collaborate and stay organized as your project grows. All the best practices and tools
are used to help you save days of mundane setup and tooling! This Django boilerplate/starter template will help you or
your team deploy your site to production in minutes instead of days.

To get started, jump to the [installation](#installation) section or keep reading to learn more about the included
features.
<!--intro-end-->

<!--readme-start-->

## ✨ Features

### 🧑‍💻 Best Practices

* [Environs](https://github.com/sloria/environs) - Used for managing environment variables
* [Docker](https://www.docker.com/) - Docker Compose for development and a multi-stage Dockerfile for production ready
  Docker image
* [UV](https://github.com/astral-sh/uv) - Used to maintain python requirements
* [Just](https://github.com/casey/just) - Popular tool for running common commands (make equivalent)

### 📦️ Django Packages

* [Django 5](https://www.djangoproject.com/) - Latest version of Django
* [Celery](http://docs.celeryproject.org/) - Most popular task runner for running asynchronous tasks in the background
* [Custom User Model][custom_user_model] - Custom user model so that the user model can be easily extended
* [Django Allauth](http://www.intenct.nl/projects/django-allauth/) - The most popular package for adding authentication
  workflows to a Django project
* [Django Crispy Forms](https://github.com/django-crispy-forms/django-crispy-forms) - The most popular helper for working with Django forms
* [Django Alive](https://github.com/lincolnloop/django-alive/) - A simple health check package for Django
* [Django Maintenance Mode](https://github.com/fabiocaccamo/django-maintenance-mode) - A simple maintenance mode package for Django

[custom_user_model]: https://docs.djangoproject.com/en/stable/topics/auth/customizing/#substituting-a-custom-user-model

### 🔧 Python Testing Tools

* [Pytest](https://docs.pytest.org/) - The most popular Python test runner in the Python community
* [Pytest Django](https://pytest-django.readthedocs.io/en/latest/index.html) - A Django plugin for Pytest
* [Pytest-cov](https://pytest-cov.readthedocs.io) - Adds code coverage to tests
* [Model Bakery](https://github.com/model-bakers/model_bakery) - A faster way to create model instances for tests
* [Django Test Plus](https://github.com/revsys/django-test-plus/) - Helper functions to write tests faster

### 🩺 Code Quality, Formatting, and Linting Tools

* [Ruff](https://github.com/charliermarsh/ruff) - Python formatting and linting. Lighting fast because it's written in Rust! Replaces Black and other tools.
* [Mypy](http://mypy-lang.org/) - Python Type checking
* [dj Lint](https://djlint.com/) - Automatic Django HTML template formatting and linting
* [Django Debug Toolbar](https://github.com/jazzband/django-debug-toolbar) - A toolbar for debugging and
  optimizing Django queries
* [Stylelint](https://stylelint.io/) - Automatic Sass formatting and linting
* [Eslint](https://eslint.org/) - Automatic Javascript formatting and linting

### 💄Frontend

* [Bootstrap 5](https://getbootstrap.com/) - A popular UI framework
* [Vite](https://vitejs.dev/) - A fast frontend build tool

### 📝 Documentation

The Django Base Site uses [MkDocs](https://www.mkdocs.org/) for documentation. You can copy the
[config file](https://github.com/epicserve/django-base-site/blob/main/config/mkdocs.yml) and the
[docs](https://github.com/epicserve/django-base-site/tree/main/docs) directory to help jumpstart the documentation for
your new project. The following are MkDocs plugins being used:

* [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) - Beautify MkDocs theme
* [mkdocstrings](https://mkdocstrings.github.io/) - Build documentation from Python docstrings
* [mkdocs-include-markdown-plugin](https://github.com/mondeja/mkdocs-include-markdown-plugin) - Include docs from other
  files
* [mkdocs-linkcheck](https://github.com/byrnereese/linkchecker-mkdocs) - Automatic link checking

## Installation

### Requirements

Before proceeding make sure you have installed [Docker](https://docs.docker.com/engine/installation/) and
[Just](https://github.com/casey/just#installation). Docker with Docker Compose is used for local development and Just is
used common project commands.

### Quickstart Install Script

Copy and past the following into your terminal to run the install script:

```bash
bash <(curl -s https://raw.githubusercontent.com/epicserve/django-base-site/main/scripts/start_new_project)
```

Running the script mostly does the same thing as manual method. The exception is that the install script has
questions to customize your new project setup.

**Note:** When starting the Django runserver it will take several seconds before the CSS styles take effect. This is
because Vite is running in dev mode which takes a few seconds to take effect.

Example output:

    $ cd ~/Sites
    $ bash <(curl -s https://raw.githubusercontent.com/epicserve/django-base-site/main/scripts/start_new_project)
    
    What is the project name slug [example]?
    What directory do you want your project in [/Users/brento/Sites/example]?

    Done.

    To start Docker Compose run:
    $ cd /Users/brento/Sites/example
    $ just start

### Manual Installation

    $ curl -LOk https://github.com/epicserve/django-base-site/archive/main.zip && unzip main
    $ mv django-base-site-main example
    $ cd example
    $ export SECRET_KEY=$(python -c "import random; print(''.join(random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789%^&*(-_=+)') for i in range(50)))")
    $ cat > .env <<EOF
    DEBUG=on
    SECRET_KEY='$SECRET_KEY'
    DATABASE_URL=postgres://postgres:@db:5432/postgres
    INTERNAL_IPS=127.0.0.1,0.0.0.0
    EOF
    $ just remove_extra_files
    $ find ./public -name ".keep" | xargs rm -rf
    $ just start

## Usage

The Django Base Site comes with Just recipes for all the most common commands and tasks that an engineer will use during
development. To see the full list of commands run `just` in the root of the project directory. The following is an
abbreviated list of the most common commands.

```
build_assets                 # Build frontend assets
clean                        # Remove build files, python cache files and test coverage data
collectstatic                # Run Django's collectstatic management command
format                       # Format all code
lint                         # Lint everything
upgrade_python_requirements  # Run pip-compile make the requirement files
open_coverage                # Run the django test runner with coverage
start                        # Start docker-compose
start_with_docs              # Start docker-compose with docs
stop                         # Stop all docker-compose services
test                         # Run the Django test runner without coverage
```

## Deploying to Production

The Django base site is designed to be production ready because it comes with a production
ready [multi-stage Dockerfile](https://github.com/epicserve/django-base-site/blob/main/config/docker/Dockerfile).
You can also read a [blog post](https://epicserve.com/django/2022/12/30/using-flyio-with-the-django-base-site.html)
about using it with fly.io. If you want to blog about using the Django Base Site with other PaaS providers, please let
me know, and I can link to the post here.

## Contribute

1. Look for an open [issue](https://github.com/epicserve/django-base-site/issues) or create new issue to get a dialog
   going about the new feature or bug that you've discovered.
2. Fork the [repository](https://github.com/epicserve/django-base-site) on GitHub to start making your changes to the
   main branch (or branch off of it).
4. Make a pull request.

<!--readme-end-->
