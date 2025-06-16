#!/bin/bash
set -e  # Stop the script if any command fails

echo "Migrating database"
uv run manage.py migrate --noinput

# Choose the server based on DEBUG
if [[ "$DEBUG" =~ ^(1|true|True|TRUE|on|yes)$ ]]; then
  echo "Starting Django development server"
  uv run manage.py runserver 0.0.0.0:8000
else
  echo "Collecting static files"
  uv run manage.py collectstatic --noinput
  echo "Starting Uvicorn server"
  uv run uvicorn config.asgi:application --host 0.0.0.0 --port 8000
fi