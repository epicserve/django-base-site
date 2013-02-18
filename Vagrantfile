Vagrant::Config.run do |config|

    # Setup the box
    # Add the box with the following before running vagrant up
    # vagrant box add lucid32 http://files.vagrantup.com/lucid32.box
    config.vm.box = "lucid32"

    config.vm.forward_port 8000, 8000
    config.vm.customize do |vm|
        vm.memory_size = 256
    end

    config.vm.provision :chef_solo do |chef|
        chef.cookbooks_path = "config/chef/cookbooks"
        chef.add_recipe("dev")
    end

end