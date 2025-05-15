#!/bin/bash

set -e  # Stop the script if any command fails

MAX_WAIT=60  # Maximum waiting time (in seconds)
WAIT_TIME=0

echo "Waiting for PostgreSQL to be ready..."

until nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
  sleep 0.1
  WAIT_TIME=$((WAIT_TIME + 1))
  if [ "$WAIT_TIME" -ge "$((MAX_WAIT * 10))" ]; then  # Multiply MAX_WAIT by 10 for 0.1 second intervals
    echo "Timeout reached ($MAX_WAIT seconds). PostgreSQL is not responding. Exiting."
    exit 1
  fi
done

echo "PostgreSQL is up and running!"

# Migrate the database
python3 manage.py migrate --noinput

# Choose the server based on DEBUG
if [[ "$DEBUG" =~ ^(1|true|True|TRUE|on|yes)$ ]]; then
  echo "Starting Django development server"
  exec python manage.py runserver 0.0.0.0:8000
else
  echo "Collecting static files"
  python3 manage.py collectstatic --noinput
  echo "Starting Gunicorn production server"
  exec gunicorn config.wsgi:application --bind 0.0.0.0:8000
fi
