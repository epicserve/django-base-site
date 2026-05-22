import 'config/base.just'

project_slug := 'django-base-site'

# List available commands
@_default:
    just -l

# Create or regenerate .env file from .env.toml schema
@create_env:
    uvx epicenv@1.6.2 create

# Create a Django superuser via epicenv (idempotent). Default: reads credentials
# from DJANGO_SUPERUSER_USERNAME / _EMAIL / _PASSWORD in .env, and skips when
# they're blank so `just init` is safe to run before you've decided on a
# superuser strategy. To source from a secrets manager instead, replace the
# body with a pipeline that pipes JSON credentials into `epicenv create-superuser`.
# Example for 1Password:
#
#     create_superuser:
#         #!/usr/bin/env bash
#         docker compose up --wait -d web
#         uvx epicenv secrets get op://Private/django-admin \
#             --fields username,email,password \
#             | docker compose exec -T web epicenv create-superuser
create_superuser:
    #!/usr/bin/env bash
    set -e
    if [ -z "${DJANGO_SUPERUSER_USERNAME:-}" ]; then
        echo "Skipping superuser creation: DJANGO_SUPERUSER_USERNAME is blank. Set credentials in .env or edit the create_superuser recipe to pipe from a secrets manager."
        exit 0
    fi
    docker compose up --wait -d web
    docker compose exec \
        -e DJANGO_SUPERUSER_USERNAME \
        -e DJANGO_SUPERUSER_EMAIL \
        -e DJANGO_SUPERUSER_PASSWORD \
        web epicenv create-superuser

# Remove extra Django Base Site files not needed in a new project
@clean_extra_files:
    rm -f LICENSE.md
    rm -f README.md
    rm -f CHANGELOG.md
    rm -rf docs/
    rm -rf .github/
    rm -rf .readthedocs.yaml
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
