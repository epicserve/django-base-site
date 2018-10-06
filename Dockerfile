FROM python:3.6.6-alpine3.7

# This prevents Python from writing out pyc files
ENV PYTHONDONTWRITEBYTECODE 1

# This keeps Python from buffering stdin/stdout
ENV PYTHONUNBUFFERED 1

ENV PYTHONPATH /code

WORKDIR /code

# Upadate Apline Linux and install system packages
# build-base - C and C++ compiliers needs for some python packages
# python-dev - Needed for building C extensions for CPython
# postgresql-dev - Contains the header files needed for installing psycopg2-binary
# libffi-dev - Needed for crytography packages like bcrypt
RUN apk update \
    && apk add build-base python-dev postgresql-dev libffi-dev

# Install Python packages
COPY Pipfile .
COPY Pipfile.lock .
RUN set -ex \
    && pip install pipenv --upgrade \
    && pipenv install --deploy --dev --system
