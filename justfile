import 'config/base.just'

# List available commands
@_default:
    just -l

# Remove extra Django Base Site files not needed in a new project
@clean_extra_files:
    rm -f LICENSE.md
    rm -f README.md
    rm -r scripts/start_new_project

# Upgrade both Python and Node
@upgrade_all_packages:
    # kill all running containers
    docker stop $(docker ps -a -q) || true
    # remove all stopped containers
    docker rm $(docker ps -a -q) || true
    just upgrade_python_requirements
    just upgrade_node_requirements
    docker compose build
    docker compose run --rm node npm ci
    just pre_commit
