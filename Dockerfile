FROM python:3.6.3

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

COPY . /code/

EXPOSE 8000

CMD manage.py runserver 0.0.0.0:8000
