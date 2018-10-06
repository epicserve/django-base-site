#!/bin/bash

DOWNLOAD_LOCATION='https://github.com/epicserve/django-base-site/archive/master.zip'
PROJECT_NAME_SLUG_DEFAULT='example'
PROJECT_NAME_SLUG='example'
PROJECT_DIRECTORY_DEFAULT="$(pwd)/$PROJECT_NAME_SLUG_DEFAULT"
PROJECT_DIRECTORY=''
GREEN=$(tput -Txterm setaf 2)
YELLOW=$(tput -Txterm setaf 3)
WHITE=$(tput -Txterm setaf 7)
RESET=$(tput -Txterm sgr0)

function ask_yes_or_no_default_no() {
    read -r -p "${GREEN}$1${RESET} ${WHITE}(y/N)${RESET}${GREEN}?${RESET} " response
    response=${response,,} # tolower
    if [[ $response =~ ^(no|n| ) ]] || [[ -z $response ]]; then
        echo "no"
    else
        echo "yes"
    fi
}

function ask_yes_or_no_default_yes() {
    read -r -p "${GREEN}$1${RESET} ${WHITE}(Y/n)${RESET}${GREEN}?${RESET} " response
    response=${response,,} # tolower
    if [[ $response =~ ^(yes|y| ) ]] || [[ -z $response ]]; then
        echo "yes"
    else
        echo "no"
    fi
}

get_project_name_slug() {
  echo -n "${GREEN}What is the project name slug${RESET} ${WHITE}[$PROJECT_NAME_SLUG_DEFAULT]${RESET}${GREEN}?${RESET} "
  read PROJECT_NAME_SLUG
  if [ -z "$PROJECT_NAME_SLUG" ]; then
    PROJECT_NAME_SLUG=$PROJECT_NAME_SLUG_DEFAULT
  fi
}

get_project_directory() {
  PROJECT_DIRECTORY_DEFAULT="$(pwd)/$PROJECT_NAME_SLUG"
  echo -n "${GREEN}What directory do you want your project in${RESET} ${WHITE}[$PROJECT_DIRECTORY_DEFAULT]${RESET}${GREEN}?${RESET} "
  read PROJECT_DIRECTORY
  if [ -z "$PROJECT_DIRECTORY" ]; then
    PROJECT_DIRECTORY=$PROJECT_DIRECTORY_DEFAULT
  fi
}

echo ""
get_project_name_slug
get_project_directory

curl -LOk $DOWNLOAD_LOCATION && unzip master
mkdir -p $PROJECT_DIRECTORY
mv django-base-site-master/* $PROJECT_DIRECTORY/
rm -rf django-base-site-master
rm master.zip
cd $PROJECT_DIRECTORY

SECRET_KEY=$(python -c "import random; print(''.join(random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789%^&*(-_=+)') for i in range(50)))")
cat > .env <<EOF
DEBUG=on
SECRET_KEY='$SECRET_KEY'
EMAIL_HOST='smtp.planetspaceball.com'
EMAIL_HOST_USER='skroob@planetspaceball.com'
EMAIL_HOST_PASSWORD='12345'
DEFAULT_FROM_EMAIL="President Skroob <skroob@planetspaceball.com>"
EOF

make remove_extra_files
USING_VAGRANT="no"
USING_COMPOSE="yes"
if [[ "no" = $(ask_yes_or_no_default_no "Are going to use Vagrant") ]]; then
    make remove_vagrant
else
    USING_VAGRANT="yes"
fi

if [[ ${USING_VAGRANT} = "no" ]] && [[ "no" = $(ask_yes_or_no_default_yes "Are going to use Docker Compose") ]]; then
    make remove_docker_compose
    USING_COMPOSE="no"
fi

if [[ "no" = $(ask_yes_or_no_default_yes "Are going to Heroku for deployment") ]]; then
    make remove_heroku
fi

if [[ ${USING_VAGRANT} = "no" ]] && [[ ${USING_COMPOSE} = "no"  ]]; then

    pipenv install --dev --python $(which python)
    pipenv run $PROJECT_DIRECTORY/manage.py migrate
    pipenv run $PROJECT_DIRECTORY/manage.py createsuperuser
    echo ""
    echo "Done."
    echo ""
    echo "To start the Django runserver in your new project:"
    echo "$ cd $PROJECT_DIRECTORY"
    echo "$ npm i"
    echo "$ pipenv run ./manage.py runserver"

elif [[ ${USING_VAGRANT} = "yes" ]]; then

    echo ""
    echo "Done."
    echo ""
    echo "WARNING: Vagrant is no longer supported and will eventually be removed."
    echo ""
    echo "To start Vagrant run:"
    echo "$ cd $PROJECT_DIRECTORY"
    echo "$ vagrant up"
    echo ""

elif [[ ${USING_COMPOSE} = "yes" ]]; then

    echo ""
    echo "Done."
    echo ""
    echo "To start Docker Compose run:"
    echo "$ cd $PROJECT_DIRECTORY"
    echo "$ docker-compose up"
    echo ""

fi
