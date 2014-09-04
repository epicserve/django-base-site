# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  # If you haven't setup a vagrant box yet with the following base box it will
  # download it from https://vagrantcloud.com/ubuntu/trusty64
  config.vm.box = "ubuntu/trusty64"
  config.vm.network "forwarded_port", guest: 8000, host: 8000
  config.ssh.forward_agent = true
  config.vm.provision "shell", path: "config/vagrant/base.sh"

  config.vm.provider "virtualbox" do |v|
    v.memory = 512
  end

end
