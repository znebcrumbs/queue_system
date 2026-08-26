#!/usr/bin/env bash
set -euo pipefail

if [ ! -f .env ]; then
  echo "Create a .env file from .env.example before running this installer."
  exit 1
fi

python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate --settings=config.settings.prod
python manage.py collectstatic --noinput --settings=config.settings.prod
python manage.py createsuperuser --settings=config.settings.prod
