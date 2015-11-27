#!/bin/sh
set -x

cd /vagrant

# INSTALL APT PACKAGES
sudo aptitude -y update
sudo aptitude -y upgrade
sudo aptitude install -y git python-pip python-dev libmysqlclient-dev htop
sudo pip install -r config/requirements/dev.txt

# CUSTOMIZE THE PROFILE
cat >> /home/vagrant/.bashrc << EOF

alias drs='/vagrant/manage.py runserver 0.0.0.0:8000'
alias d='/vagrant/manage.py'
complete -cf sudo

cd /vagrant

echo ""
echo "Commands:"
echo "drs - Start Django's runserver"
echo "d   - Alias to Django's manage.py"
echo ""
EOF

# SETUP THE LOCAL SETTINGS FILE
if [ ! -f /vagrant/config/settings/local.py ]; then
    python /vagrant/config/create_local_settings_file.py
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
