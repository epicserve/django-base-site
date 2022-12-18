# ------------------------------------------------------------
# STAGE 1: Build Python requirements layer
# ------------------------------------------------------------
FROM python:3-buster as python-requirements

ARG ENV_NAME=dev

ENV \
    # This prevents Python from writing out pyc files \
    PYTHONDONTWRITEBYTECODE=1 \
    # This keeps Python from buffering stdin/stdout \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv

RUN set -ex \
    && python3 -m venv $VIRTUAL_ENV \
    && $VIRTUAL_ENV/bin/pip install -U setuptools wheel pip

# Install Python packages
COPY config/requirements/$ENV_NAME.txt ./config/requirements/$ENV_NAME.txt

RUN set -ex \
    && $VIRTUAL_ENV/bin/pip install -r config/requirements/$ENV_NAME.txt \
    && rm -rf /root/.cache/


# ------------------------------------------------------------
# STAGE 2: Dev layer
# ------------------------------------------------------------
FROM python:3-slim-buster as dev

# Set the locale
# libxml2-dev is needed for uwsgi in the production stage
# mime-support install (/etc/mime.types) which is needded uWSGI to server static files with the correct mime types
RUN apt-get update \
    && apt-get install -y locales libxml2-dev mime-support \
    && echo "LC_ALL=en_US.UTF-8" >> /etc/environment \
    && echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen \
    && echo "LANG=en_US.UTF-8" > /etc/locale.conf \
    && locale-gen en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/opt/venv
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    DJANGO_SETTINGS_MODULE=config.settings \
    PYTHONPATH=/srv/app \
    TERM=xterm-color \
    PATH=$VIRTUAL_ENV/bin:${PATH}

RUN set -ex \
    && groupadd -r app && useradd --uid=1000 --create-home --home-dir=/home/app --no-log-init -r -g app app

COPY --from=python-requirements --chown=app:app $VIRTUAL_ENV $VIRTUAL_ENV

USER app

WORKDIR /srv/app

EXPOSE 8000/tcp 8001/tcp

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


# ------------------------------------------------------------
# STAGE 3: Javascript assets layer
# ------------------------------------------------------------
FROM node:16.18 as js_assets

WORKDIR /srv/app

COPY package.json package-lock.json ./
COPY src src

# Install Node packages
RUN npm ci \
    && npm run build \
    && ls -la public/static/dist/


# ------------------------------------------------------------
# STAGE 4: Prod
# ------------------------------------------------------------

FROM dev as prod

WORKDIR /srv/app

USER app

COPY . .

RUN SECRET_KEY=e python manage.py collectstatic --no-input

COPY --from=js_assets --chown=app:app /srv/app/public/static/ ./collected_static

CMD ["uwsgi", "--ini", "config/uwsgi.ini", "--http", "0.0.0.0:8080"]
