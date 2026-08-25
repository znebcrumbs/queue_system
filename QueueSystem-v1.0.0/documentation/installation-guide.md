# Installation Guide

## Overview

This guide explains how to install the QueueSystem v1.0.0 application in a production environment. It is written for the technical administrator responsible for hosting, database configuration, TLS, and secure deployment.

## Requirements

- Linux server or equivalent host
- Python 3.12 or higher
- PostgreSQL 16 or higher
- access to a valid domain and HTTPS certificate
- ability to manage environment variables securely

## Step 1 — Prepare the server

Update the operating system and install dependencies.

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip postgresql postgresql-client nginx
```

## Step 2 — Create the database

Create the database and a dedicated user.

```sql
CREATE DATABASE queue_system;
CREATE USER queue_user WITH PASSWORD 'change-me';
GRANT ALL PRIVILEGES ON DATABASE queue_system TO queue_user;
```

## Step 3 — Configure the environment

Copy `.env.example` to `.env` and replace the sample values with the real production values.

Required values:

- `SECRET_KEY`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL` or PostgreSQL variables
- `KIOSK_API_KEY`
- `DEBUG=False`

## Step 4 — Install Python dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 5 — Run migrations

```bash
python manage.py migrate --settings=config.settings.prod
```

## Step 6 — Collect static files

```bash
python manage.py collectstatic --noinput --settings=config.settings.prod
```

## Step 7 — Create the administrator user

```bash
python manage.py createsuperuser --settings=config.settings.prod
```

## Step 8 — Configure HTTPS and domain

- set the DNS record for the application domain
- configure the HTTPS certificate
- set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` to the production values
- enable reverse proxy forwarding to the application server

## Step 9 — Launch the application

Use your preferred process manager, reverse proxy, or Docker runtime.

Example:

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

## Verification

Once the system is running, verify the following:

- the homepage loads over HTTPS
- admin login works
- queue dashboard loads correctly
- kiosk service operations work
- no database connection errors appear in the logs

## Troubleshooting

### Invalid host header

Check the `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` values in `.env`.

### Database connection failure

Confirm PostgreSQL is running and the credentials match the environment file.

### HTTPS redirect issues

Ensure the reverse proxy forwards the `X-Forwarded-Proto` header and `SECURE_SSL_REDIRECT=True` is enabled in production.
