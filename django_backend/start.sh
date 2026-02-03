#!/bin/sh

# Exit on error
set -e

echo "Starting server on PORT=$PORT"

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Starting Gunicorn server..."
exec gunicorn chemical_visualizer.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
