#!/bin/sh
set -eu

DB_PATH="${DATABASE_PATH:-/app/db.sqlite3}"
DB_DIR="$(dirname "$DB_PATH")"
MEDIA_DIR="${MEDIA_ROOT_PATH:-/app/media}"

mkdir -p "$DB_DIR" "$MEDIA_DIR"

echo "Applying Django migrations..."
python manage.py migrate --noinput

echo "Starting Gunicorn..."
exec gunicorn fzboard.wsgi:application --bind 0.0.0.0:8000 --workers "${GUNICORN_WORKERS:-3}"
