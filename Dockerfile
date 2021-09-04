FROM python:3-slim-buster


ENV \
    # This prevents Python from writing out pyc files \
    PYTHONDONTWRITEBYTECODE=1 \
    # This keeps Python from buffering stdin/stdout \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/code

WORKDIR /code

# build-essential - C compiler for building packages like uwsgi
# python-dev - Needed for building C extensions for CPython
# postgresql-server-dev-all - Contains the header files needed for installing psycopg2-binary
# libffi-dev - Needed for crytography packages like bcrypt
RUN apt update \
    && apt install -y build-essential python-dev postgresql-server-dev-all libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements-dev.txt ./

RUN set -ex \
    && pip install --upgrade pip \
    && pip install pip-tools --upgrade \
    && pip install -r /code/requirements-dev.txt \
    && cp /etc/skel/.bashrc /root/.bashrc
