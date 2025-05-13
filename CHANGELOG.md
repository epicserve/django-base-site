# CHANGELOG


## 2025-05-13

### Changed

* Changed Pytest to run tests using Postgres instead of SQLite.


## 2025-05-03

### Changed

* Switch to using `uv sync` and the `uv.lock` with `pyproject.toml` instead of `uv pip` with `*.in` requirement files.


## 2025-04-13

### Changed

* Make the default gravatar cartoon-style silhouetted outline of a person


## 2025-04-12

### Changed

* Improved the sign in UI/UX


## 2025-04-05

### Changed

* Switch to using `docker compose exec` instead of `docker compose run` for faster Just commands
* Switch to using the base_entrance.html template for Allauth, so templates that aren't overridden like the signup_closed.html template still work
* Update the Githut Action that creates a PR for Python upgrades so that it bolds upgrades greater than a patch

### Fixed

* Fix a JS exception in color picker
* Remove the extra double quote in the Github Action that creats a PR for Python upgrades
* Fix the browser trying to load the Favicon
* Fix the case for "AS" in the docker config file
* Fix linting errors


## 2024-10-04

### Fixed

* The quickstart script not replacing the project name in the compose.yml file.


## 2024-10-02

### Changed

* Updated ESLint to format config files
* Suppress SASS warnings until Bootstrap v5.3.4 is released


## 2024-10-02

### Changed

* Use [python-json-logger](https://github.com/madzak/python-json-logger) and [readable-log-formatter](https://github.com/ipmb/readable-log-formatter) for for better log parsing with JSON


## 2024-03-16

### Added

* Added Just commands to dump and restore the database


## 2024-03-11

### Changed

* Renamed the Just command build_assets to build_frontend
* Moved all common/base Just commands to the config/base.just file


## 2024-02-26

### Changed

* Switched to Ruff for linting and formatting Python. This replaces Bandit, Black, and isort.


## 2024-02-24

### Changed

* Switched to using UV instead of pip/pip-tools for managing Python requirements


## 2024-01-06

### Changed

* Upgraded to Python 3.12


## 2023-12-31

### Added

* Added the Just command update_everything to upgrade Python and Node

### Changed

* Upgraded to Django 5.0


## 2023-12-26

### Changed

* Refactor and clean up the vite_asset template tag
* Add tests for the vite_asset and vite_hmr_client template tags


## 2023-12-24

### Changed

* Upgrade from Vite 4.5 to 5.0 


## 2023-10-07

### Added

* Add the Django Maintenance Mode package


## 2023-09-23

### Added

* Add a gravatar property to the user model

### Changed

* Make the layout and style better for SaaS projects


## 2023-09-16

### Changed

* Updated Redis configuration settings to allow for a REDIS_PREFIX

### Added

* Added Django-alive for health checks
* Added a uwsgi.ini config file


## 2023-09-10

### Changed

* Upgrade the Python container from Debian buster to bookworm and pin the Python version to 3.11.*.


## 2023-08-31

### Changed

* Upgrade to version 3 of the Compose file
* Switch to using a named volume for node_modules.
* Switch to always upgrade npm on build


## 2023-08-29

### Changed

* Changed to using a root user for local development. This fixes an issue that was happening where Vite and other JS
  related tools where throwing write permission errors when running because the web service would create files as a
  non-privileged app user and then JS tools would run as a non-privileged user and then try to write to
  directories owned by root.


## 2023-06-01

### Changed

* Remove the Docker Compose volume for node for more consistent builds. This fixes the problem where sometimes you had
  to run `docker compose run node npm install` after running `docker compose build` to install the node modules into the
  local node volume. Instead the node modules are always installed into the docker image.

### Fixed

* Fixed Vite not being available after changes to package.json. This fixes [#289](https://github.com/epicserve/django-base-site/issues/289)


## 2023-04-01

### Added

* Add a pre_commit command to the justfile to run the lint, format, and test commands


## 2022-01-14

### Changed

* Removed the "Successfully signed in as" message after a user has signed in by add the ACCOUNT_SHOW_POST_LOGIN_MESSAGE
  setting with it set to False by default.
* By default, set ACCOUNT_EMAIL_VERIFICATION to "none" so that new hobby apps don't require transactional email set up.
* Changed ACCOUNT_USERNAME_REQUIRED to False and ACCOUNT_AUTHENTICATION_METHOD to "email" so you can signup and signin
  with just your email address.
* Changed ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE to False for a nicer sign-up experience

### Added

* Added the adapter apps.accounts.auth_adapter.AccountAdapter to add the new custom settings
* The ACCOUNT_SIGNUP_OPEN setting set it to false so signup is closed by default
* Bash aliases and Django bash completion


## 2022-12-31

### Added

* A color picker to toggle between dark and light mode

### Changed

* Upgraded to Bootstrap 5.3.0-alpha1 in order to add the color picker 


## 2022-12-27

### Added

* The packages django-test-plus and model-bakers
* More tests
* The upgrade_packages Just recipe
* Just recipes for removing docker containers, images, volumes
* Bandit for automatic security scanning


## 2022-12-26

### Added

* Just recipe, build_assets

### Changed

* Switch from the using docker-compose to using docker compose
* Updated Django settings, so you can use config/settings/test_runner.py for pytest
* Add the lock suffix to generated Python requirement files
* Clean up and add more arguments to the start project script


## 2022-12-18

### Added

* Instructions on how to deploy to Fly.io

### Changed

* Make changes to settings to make it easier to deploy to platforms like Fly.io


## 2022-12-17

### Changed

* Switched the session backend from django-redis-sessions to the native django.contrib.sessions.backends.cache backend.
* Switched from using django-redis-cache for parsing a REDIS_URL to using the native django.core.cache.backends.redis.RedisCache backend.
* Move the vite asset tags to the bottom script block.


## 2022-12-12

### Added

* Missing accounts migration

### Changed

* Update the Dockerfile so it could be used for production builds


## 2022-12-11

### Changed

* Upgrade to Vite 4.0


## 2022-12-10

### Changed

* Upgrade to Django 4.1
* Change python version to 3.11
* Move the Javascript config files for eslint, stylelint, and Vite from the root directory to src/config
* Change the mkdocs port from 5000 to 4000 since Airtunes/Airplay are taking that port
* Move the mkdocs.yml config to the docs directory
* Move the Docker files and requirement files under the config directory
* Switch from using Flake8 to using Ruff


## 2022-12-08

### Changed

* Switch from using Make for common commands to Just
