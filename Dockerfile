FROM python:3.6.6-alpine3.7

# This prevents Python from writing out pyc files
ENV PYTHONDONTWRITEBYTECODE 1

# This keeps Python from buffering stdin/stdout
ENV PYTHONUNBUFFERED 1

ENV PYTHONPATH /code

WORKDIR /code

# Upadate Apline Linux and install system packages
RUN apk update \
    && apk add git python-dev postgresql-dev libffi-dev build-base

# Install Python packages
COPY Pipfile .
COPY Pipfile.lock .
RUN set -ex \
    && pip install pipenv --upgrade \
    && pipenv install --deploy --dev --system
