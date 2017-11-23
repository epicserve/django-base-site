#!/bin/bash

DOWNLOAD_LOCATION='https://github.com/epicserve/django-base-site/archive/master.zip'
PROJECT_NAME_SLUG_DEFAULT='example'
PROJECT_NAME_SLUG='example'
PROJECT_DIRECTORY_DEFAULT="$(pwd)/$PROJECT_NAME_SLUG_DEFAULT"
PROJECT_DIRECTORY=''

get_project_name_slug() {
  echo -n "What is the project name slug? [$PROJECT_NAME_SLUG_DEFAULT]: "
  read PROJECT_NAME_SLUG
  if [ -z "$PROJECT_NAME_SLUG" ]; then
    PROJECT_NAME_SLUG=$PROJECT_NAME_SLUG_DEFAULT
  fi
}

get_project_directory() {
  PROJECT_DIRECTORY_DEFAULT="$(pwd)/$PROJECT_NAME_SLUG"
  echo -n "What directory do you want your project in [$PROJECT_DIRECTORY_DEFAULT]? "
  read PROJECT_DIRECTORY
  if [ -z "$PROJECT_DIRECTORY" ]; then
    PROJECT_DIRECTORY=$PROJECT_DIRECTORY_DEFAULT
  fi
}

get_project_name_slug
get_project_directory

curl -LOk $DOWNLOAD_LOCATION && unzip master
mv django-base-site-master $PROJECT_DIRECTORY
rm master.zip
cd $PROJECT_DIRECTORY
pipenv install --dev --python $(which python3)
SECRET_KEY=$(python -c "import random; print(''.join(random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789%^&*(-_=+)') for i in range(50)))")

cat > .env <<EOF
DEBUG=on
SECRET_KEY='$SECRET_KEY'
EMAIL_HOST='smtp.planetspaceball.com'
EMAIL_HOST_USER='skroob@planetspaceball.com'
EMAIL_HOST_PASSWORD='12345'
DEFAULT_FROM_EMAIL="President Skroob <skroob@planetspaceball.com>"
EOF

pipenv run $PROJECT_DIRECTORY/manage.py migrate
pipenv run $PROJECT_DIRECTORY/manage.py createsuperuser

echo "
To start the Django runserver in your new project:
$ cd $PROJECT_DIRECTORY
$ pipenv shell
$ ./manage.py runserver
"

make clean
unset PROJECT_NAME_SLUG
unset PROJECT_DIRECTORY
