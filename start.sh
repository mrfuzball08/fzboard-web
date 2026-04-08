#!/bin/bash
set -e

echo "Building frontend assets..."
bun run build

echo "Applying Django migrations..."
python manage.py migrate --noinput

echo "Starting Django server..."
python manage.py runserver 0.0.0.0:8000
