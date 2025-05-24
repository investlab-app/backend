#!/bin/bash
set -e  # Stop the script if any command fails

echo "Migrating database"
python3 manage.py migrate --noinput

echo "Collecting static files"
python3 manage.py collectstatic --noinput

echo "Starting Uvicorn server"
uvicorn config.asgi:application --host 0.0.0.0 --port 8000
