# CHANGELOG

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