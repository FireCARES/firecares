#!/bin/bash

python manage.py collectstatic --noinput

chmod -R 0755 /webapps/

nginx

# Start Gunicorn processes
# Gunicorn requires a reverse proxy to serve
# static content...
echo Starting Gunicorn.
exec gunicorn firecares.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3
