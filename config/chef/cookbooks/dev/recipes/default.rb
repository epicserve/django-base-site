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

# Add /vagrant to the python path
cookbook_file "/usr/local/virtualenvs/django-base-site/lib/python2.6/site-packages/_virtualenv_path_extensions.pth" do
    source "_virtualenv_path_extensions.pth"
    owner "vagrant"
    group "root"
    mode 0664
end

bash "run_syncdb" do
      user "vagrant"
      cwd "/tmp"
      code <<-EOH
      source /usr/local/virtualenvs/django-base-site/bin/activate
      SECRET_KEY='my-secret-key-only-for-development' django-admin.py syncdb --noinput --migrate --settings='config.settings.development'
      EOH
end
