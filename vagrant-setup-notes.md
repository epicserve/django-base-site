Do the following to setup a new dev vagrant server:

    $ vagrant up
    $ sudo aptitude update
    $ sudo aptitude -y upgrade
    $ sudo aptitude -y install python-setuptools
    $ sudo easy_install pip
    $ sudo pip install virtualenvwrapper
    $ export WORKON_HOME=/usr/local/virtualenvs
    $ sudo mkdir -p $WORKON_HOME
    $ sudo chown vagrant:vagrant $WORKON_HOME
    $ source /usr/local/bin/virtualenvwrapper.sh
    $ vi /home/vagrant/.profile

    export WORKON_HOME=/usr/local/virtualenvs
    source /usr/local/bin/virtualenvwrapper.sh

    # Setup Virtualenvwrapper
    export WORKON_HOME=/usr/local/virtualenvs
    source /usr/local/bin/virtualenvwrapper.sh

    # Django Settings
    export DJANGO_SETTINGS_MODULE='config.settings.development'
    export SECRET_KEY='my-secret-key-only-for-development'
    alias d=django-admin.py
    alias drs='django-admin.py runserver 0.0.0.0:8000'

    # Make the prompt red
    PS1='\[\e]0;\u@\h: \w\a\]${debian_chroot:+($debian_chroot)}\[\033[01;31m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '

    cd /vagrant/

    $ source .profile
    $ mkvirtualenv --distribute django-base-site
    $ pip install -r config/requirements/dev.txt
    $ export DJANGO_SETTINGS_MODULE=config.settings.development
    $ add2virtualenv .
    $ django-admin.py syncdb --noinput
    $ drs
