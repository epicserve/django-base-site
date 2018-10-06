#!/bin/bash

DOWNLOAD_LOCATION='https://github.com/epicserve/django-base-site/archive/master.zip'
PROJECT_NAME_SLUG_DEFAULT='example'
PROJECT_NAME_SLUG='example'
PROJECT_DIRECTORY_DEFAULT="$(pwd)/$PROJECT_NAME_SLUG_DEFAULT"
PROJECT_DIRECTORY=''

function ask_yes_or_no_default_no() {
    read -r -p "$1 ([Y]es or [N]o [Default]) " response
    response=${response,,} # tolower
    if [[ $response =~ ^(no|n| ) ]] || [[ -z $response ]]; then
        echo "no"
    else
        echo "yes"
    fi
}

function ask_yes_or_no_default_yes() {
    read -r -p "$1 ([Y]es [Default] or [N]o) " response
    response=${response,,} # tolower
    if [[ $response =~ ^(yes|y| ) ]] || [[ -z $response ]]; then
        echo "yes"
    else
        echo "no"
    fi
}

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

If you don't plan on using Heroku for deployment, you can run 'make remove_heroku' to remove Heroku config files.
"

unset PROJECT_NAME_SLUG
unset PROJECT_DIRECTORY

make remove_extra_files
if [[ "no" = $(ask_yes_or_no_default_no "Are going to use Vagrant?") ]]; then
    make remove_vagrant
else
    echo "Warning: Vagrant is no longer supported and may or may not work.\n"
fi

if [[ "no" = $(ask_yes_or_no_default_yes "Are going to use Docker Compose?") ]]; then
    make remove_docker_compose
fi
