# ------------------------------------------------------------
# STAGE 1: Build Python requirements layer
# ------------------------------------------------------------
FROM python:3-buster as python-requirements

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
COPY requirements-dev.txt ./

RUN set -ex \
    && $VIRTUAL_ENV/bin/pip install -r requirements-dev.txt \
    && rm -rf /root/.cache/


# ------------------------------------------------------------
# STAGE 2: Dev layer
# ------------------------------------------------------------
FROM python:3-slim-buster

# Set the locale
RUN apt-get update \
    && apt-get install -y locales \
    && echo "LC_ALL=en_US.UTF-8" >> /etc/environment \
    && echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen \
    && echo "LANG=en_US.UTF-8" > /etc/locale.conf \
    && locale-gen en_US.UTF-8

ENV VIRTUAL_ENV=/opt/venv
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    DJANGO_SETTINGS_MODULE=config.settings \
    PYTHONPATH=/srv/app \
    TERM=xterm-color \
    PATH=$VIRTUAL_ENV/bin:${PATH}

RUN set -ex \
    && groupadd -r app && useradd --uid=1000 --create-home --home-dir=/home/app --no-log-init -r -g app app \
    # copy the bashrc to the home and uncomment some helpful aliases \
#    && cat /etc/skel/.bashrc | awk '{sub("#alias","alias")} {print}' > /home/app/.bashrc \
    && apt-get update \
    && rm -rf /var/lib/apt/lists/*

COPY --from=python-requirements --chown=app:app $VIRTUAL_ENV $VIRTUAL_ENV
WORKDIR /srv/app

USER app

EXPOSE 8000/tcp 8001/tcp

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
