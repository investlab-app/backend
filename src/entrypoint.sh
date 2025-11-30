#!/bin/bash
set -euo pipefail # Stop the script if any command fails

# Determine if Datadog tracing is enabled
DD_TRACE_ENABLED=${DD_TRACE_ENABLED:-false}
if [[ "$DD_TRACE_ENABLED" =~ ^(1|true|True|TRUE|on|yes)$ ]]; then
    TRACE_CMD="ddtrace-run"
    echo "Datadog APM enabled"
else
    TRACE_CMD=""
    echo "Datadog APM disabled"
fi

# Choose the server based on DEBUG
if [[ "$DEBUG" =~ ^(1|true|True|TRUE|on|yes)$ ]]; then
    echo "Starting Django development server"
    uv run $TRACE_CMD manage.py runserver 0.0.0.0:8000
else
    echo "Starting Gunicorn server"
    exec uv run $TRACE_CMD gunicorn config.asgi:application \
    --bind 0.0.0.0:"${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-2}" \
    --worker-class uvicorn_worker.UvicornWorker \
    --access-logfile - \
    --error-logfile - \
    --timeout "${GUNICORN_TIMEOUT:-60}" \
    --keep-alive "${GUNICORN_KEEPALIVE:-5}"
fi
