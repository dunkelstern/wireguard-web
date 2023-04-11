#!/bin/bash

set -o allexport
source .env
set +o allexport


python manage.py migrate
python manage.py collectstatic --noinput 
gunicorn -b 0.0.0.0:8000 --workers 2 wireguard_web.wsgi:application
