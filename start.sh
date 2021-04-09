#!/bin/bash

echo '### settings begin ###'

python manage.py diffsettings --all
echo '### settings end ###'

python manage.py migrate

python manage.py collectstatic --noinput

chmod -R 0755 /webapps/

# Start Gunicorn processes
# Gunicorn requires a reverse proxy to serve
# static content...
echo Starting Gunicorn.
exec gunicorn firecares.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --log-level debug \
    --error-logfile - \
    --capture-output
