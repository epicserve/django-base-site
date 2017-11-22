#!/bin/sh
set -x

cd /vagrant

# VARIABLES
export WORKON_HOME=/usr/local/virtualenvs
export BASHRC='/home/vagrant/.bashrc'

# INSTALL APT PACKAGES
sudo apt -y update
sudo apt -y upgrade
sudo apt install -y git python3-pip python3-dev libmysqlclient-dev htop nodejs npm

# SETUP PYTHON AND THE PROJECT VIRTUALENV
pip3 install pipenv virtualenvwrapper
sudo mkdir -p $WORKON_HOME
sudo chown vagrant:vagrant $WORKON_HOME
virtualenv --python $(which python3) "$WORKON_HOME/$PROJECT_NAME"
. "$WORKON_HOME/$PROJECT_NAME/bin/activate"
pipenv install --dev

# SETUP NODE PACKAGES
npm i -g gulp
npm i

# CUSTOMIZE THE PROFILE
if [ ! $(grep "WORKON_HOME" $BASHRC) ]; then

cat >> $BASHRC << EOF

export WORKON_HOME=$WORKON_HOME
export PIP_REQUIRE_VIRTUALENV=true
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
source /usr/local/bin/virtualenvwrapper.sh

alias drs='/vagrant/manage.py runserver 0.0.0.0:8000'
alias d='/vagrant/manage.py'
complete -cf sudo

cd /vagrant
workon $PROJECT_NAME

echo ""
echo "Commands:"
echo "gulp   - Build SCSS and JS files"
echo "workon - Select a virtualenv"
echo "drs    - Start Django's runserver"
echo "d      - Alias to Django's manage.py"
echo ""
EOF

fi

# SETUP THE LOCAL .env file
if [ ! -f /vagrant/.env ]; then

export SECRET_KEY=$(python -c "import random; print(''.join(random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789%^&*(-_=+)') for i in range(50)))")
cat > .env <<EOF
DEBUG=on
SECRET_KEY='$SECRET_KEY'
EMAIL_HOST='smtp.planetspaceball.com'
EMAIL_HOST_USER='skroob@planetspaceball.com'
EMAIL_HOST_PASSWORD='12345'
DEFAULT_FROM_EMAIL="President Skroob <skroob@planetspaceball.com>"
EOF

fi

# SETUP THE DB
/vagrant/manage.py migrate

# REMOVE FILES THAT AREN'T NEEDED ANYMORE
make clean

# DONE
echo '
Done!

Now ssh to your vagrant box with `vagrant ssh` and then start the Django
development sever with the bash alias `drs`. Then go to http://127.0.0.1:8000/
in your browser to view your new base site!
'
