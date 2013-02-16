Vagrant::Config.run do |config|

    # Setup the box
    config.vm.box = "lucid32"

    config.vm.forward_port 8000, 8000
    config.vm.customize do |vm|
        vm.memory_size = 256
    end

end