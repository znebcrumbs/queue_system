#!/usr/bin/env bash
set -euo pipefail

python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate --settings=config.settings.prod
python manage.py collectstatic --noinput --settings=config.settings.prod

printf "\nCreate an admin user now with:\n"
printf "python manage.py createsuperuser --settings=config.settings.prod\n"
