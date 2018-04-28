FROM python:3.6.5

# This prevents Python from writing out pyc files
ENV PYTHONDONTWRITEBYTECODE 1

# This keeps Python from buffering stdin/stdout
ENV PYTHONUNBUFFERED 1

ENV PYTHONPATH /code

WORKDIR /code

COPY Pipfile .
COPY Pipfile.lock .

RUN set -ex \
    && pip install pipenv --upgrade \
    && pipenv install --deploy --dev --system

# Install and Setup Node based on this guide https://www.digitalocean.com/community/tutorials/how-to-install-node-js-on-debian-8
# Note in order for gulp to work with docker-compose, you'll need to add /code/node_modules to your volumes.
COPY package.json .
RUN curl -sL https://deb.nodesource.com/setup_6.x -o nodesource_setup.sh \
    && bash nodesource_setup.sh \
    && apt-get install nodejs \
    && rm nodesource_setup.sh \
    && npm i -g npm \
    && npm i -g gulp jshint \
    && npm i
