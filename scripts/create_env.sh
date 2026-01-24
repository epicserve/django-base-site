#!/usr/bin/env bash

set -e  # Exit on any error

PROJECT_NAME_SLUG=${1:-example}

function random_password() {
    local password_length=${1:-50}
    local password=$(python -c "import random; print(''.join(random.SystemRandom().choice('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789') for i in range(${password_length})))")
    echo $password
}

# Backup existing .env file if it exists
if [ -f .env ]; then
    BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE=".env.backup_${BACKUP_TIMESTAMP}"
    cp .env "$BACKUP_FILE"
    echo "Backed up existing .env to $BACKUP_FILE"
fi

# Generate passwords
SECRET_KEY=$(random_password)
POSTGRES_PASSWORD=$(random_password 12)

# Create .env file
cat > .env <<EOF
DEBUG=on
SECRET_KEY=$SECRET_KEY
POSTGRES_USER=${PROJECT_NAME_SLUG}
POSTGRES_DB=${PROJECT_NAME_SLUG}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
DATABASE_URL=postgres://\${POSTGRES_USER}:\${POSTGRES_PASSWORD}@db:5432/\${POSTGRES_DB}
INTERNAL_IPS=127.0.0.1,0.0.0.0
COMPOSE_BAKE=true
DOCKER_BUILDKIT=1
COMPOSE_DOCKER_CLI_BUILD=1
EOF

echo "Created .env file for project: $PROJECT_NAME_SLUG"
