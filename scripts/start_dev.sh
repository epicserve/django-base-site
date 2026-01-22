#!/bin/bash
# Django Development Server Startup Script
#
# This script starts the Django development server with optional debugging support.
#
# To enable debugging:
#   1. Set ENABLE_DEBUGGER=true in your .env file, OR
#   2. Set it in compose.yml under the web service environment section, OR
#   3. Run: ENABLE_DEBUGGER=true docker compose up web
#
# Once enabled, the debugger will listen on port 5678 for connections from:
#   - VS Code (use the provided launch.json configuration)
#   - LazyVim/Neovim (configure nvim-dap to connect to localhost:5678)
#   - Any other DAP-compatible editor
#
# Note: When debugging is enabled, auto-reload is disabled to prevent conflicts.
# You'll need to manually restart the server after code changes.

set -e

# Run migrations
./manage.py migrate --noinput

echo "ENABLE_DEBUGGER is set to: $ENABLE_DEBUGGER"

# Check if debugging is enabled
if [ "$ENABLE_DEBUGGER" = "true" ]; then
    echo "========================================="
    echo "Starting Django with debugger enabled"
    echo "Debugger listening on 0.0.0.0:5678"
    echo "Attach from VS Code, LazyVim, or any DAP client"
    echo "========================================="
    # Listen mode allows any DAP client to connect without blocking startup
    python -m debugpy --listen 0.0.0.0:5678 ./manage.py runserver 0.0.0.0:8000 --nothreading --noreload
else
    echo "Starting Django in normal development mode (auto-reload enabled)..."
    ./manage.py runserver 0.0.0.0:8000
fi
