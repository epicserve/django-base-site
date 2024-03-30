import 'config/base.just'

project_slug := 'django-base-site'

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
    just upgrade_python_packages
    just upgrade_node_packages
    just build
    just pre_commit

git_upgrades_output:
    #!/usr/bin/env bash
    git diff > diff.txt
    python -c "
    import re
    import os

    with open('diff.txt') as f:
        diff = f.read()

    # Find all the packages that were upgraded
    packages = re.findall(r'\+\s*([a-zA-Z0-9-]+)==([0-9\.]+)', diff)

    upgrades = []
    for pkg, new_ver in packages:
        # Find the old version of the package
        old_ver_match = re.search(r'-\s*' + re.escape(pkg) + r'==([0-9\.]+)', diff)
        if old_ver_match:
            old_ver = old_ver_match.group(1)
            upgrades.append((pkg, old_ver, new_ver))

    upgrades_str = ', '.join(f'{pkg} from {old_ver} to {new_ver}' for pkg, old_ver, new_ver in upgrades)
    print(f'Upgraded {len(upgrades)}, packages: {upgrades_str}')
    "
    rm diff.txt
