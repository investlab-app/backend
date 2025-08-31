#!/bin/bash
set -euo pipefail # Stop the script if any command fails

# echo "Make migrations"
# uv run manage.py makemigrations --noinput

echo "Migrating database"
uv run manage.py migrate --noinput

# Choose the server based on DEBUG
if [[ "$DEBUG" =~ ^(1|true|True|TRUE|on|yes)$ ]]; then
    echo "Starting Django development server"
    uv run manage.py runserver 0.0.0.0:8000
else
    echo "Collecting static files"
    uv run manage.py collectstatic --noinput
    echo "Starting Gunicorn server"
    exec uv run gunicorn config.asgi:application \
    --bind 0.0.0.0:"${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-2}" \
    --worker-class uvicorn_worker.UvicornWorker \
    --access-logfile - \
    --error-logfile - \
    --timeout "${GUNICORN_TIMEOUT:-60}" \
    --keep-alive "${GUNICORN_KEEPALIVE:-5}"
fi