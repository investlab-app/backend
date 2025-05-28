#!/bin/bash
set -e  # Stop the script if any command fails

echo "Migrating database"
python3 manage.py migrate --noinput

# Choose the server based on DEBUG
if [[ "$DEBUG" =~ ^(1|true|True|TRUE|on|yes)$ ]]; then
  echo "Starting Django development server"
  exec python manage.py runserver 0.0.0.0:8000
else
  echo "Collecting static files"
  python3 manage.py collectstatic --noinput
  echo "Starting Uvicorn server"
  uvicorn config.asgi:application --host 0.0.0.0 --port 8000
fi