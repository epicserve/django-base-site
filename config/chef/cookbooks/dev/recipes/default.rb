include_recipe "apt"
include_recipe "python"

execute "upgrade packages" do
    command "apt-get -y upgrade"
    action :nothing
end.run_action(:run)

package 'vim'
package 'python-setuptools'
package 'python'

# create virtualenvs directory
directory "/usr/local/virtualenvs" do
    owner "vagrant"
    group "vagrant"
    mode 0755
end

# install virtualenvwrapper
python_pip "virtualenvwrapper"

# add the profile file for the vagrant user
cookbook_file "/home/vagrant/.profile" do
    source "profile"
    owner "vagrant"
    group "vagrant"
    mode 0600
end

# add a virtualenv for the django-base-site project
python_virtualenv "/usr/local/virtualenvs/django-base-site" do
    owner "vagrant"
    group "vagrant"
    options "--distribute"
    action :create
end

# install python requirements for the project
python_pip "-r /vagrant/config/requirements/dev.txt" do
    virtualenv "/usr/local/virtualenvs/django-base-site"
    user "vagrant"
end

execute "Add the vagrant directory to the python path" do
    command "/usr/local/virtualenvs/django-base-site/bin/add2virtualenv /vagrant"
    user "vagrant"
end.run_action(:run)

execute "Run syncdb" do
    command "/usr/local/virtualenvs/django-base-site/bin/django-admin.py syncdb --noinput"
    user "vagrant"
    environment "DJANGO_SETTINGS_MODULE" => "config.settings.development"
end.run_action(:run)
