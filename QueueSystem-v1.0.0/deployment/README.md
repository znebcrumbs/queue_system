# Deployment Guide

## Supported deployment model

QueueSystem v1.0.0 is supported for:

- Ubuntu or Debian Linux virtual machines
- PostgreSQL 16+
- Python 3.12+
- Nginx or equivalent TLS reverse proxy
- HTTPS domain with valid certificate

## Minimum requirements

- 2 CPU cores
- 4 GB RAM
- 20 GB SSD storage
- static IP or public DNS entry
- PostgreSQL instance
- TLS certificate

## Installation process

1. Provision the server.
2. Install Python 3.12 and PostgreSQL.
3. Create the application database and dedicated user.
4. Copy `.env.example` to `.env` and complete the required values.
5. Install dependencies.
6. Run migrations.
7. Collect static files.
8. Create the administrator user.
9. Configure reverse proxy and TLS.
10. Run the application under a process manager or Docker Compose.

## Database setup

Create a PostgreSQL database and user:

```sql
CREATE DATABASE queue_system;
CREATE USER queue_user WITH PASSWORD 'change-me';
GRANT ALL PRIVILEGES ON DATABASE queue_system TO queue_user;
```

## Environment setup

The package includes a template at `.env.example`. Use it as the baseline for the production environment.

Required values include:

- `SECRET_KEY`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL` or PostgreSQL settings
- `KIOSK_API_KEY`
- `DEBUG=False`

## Migrations

```bash
python manage.py migrate --settings=config.settings.prod
```

## Static files

```bash
python manage.py collectstatic --noinput --settings=config.settings.prod
```

## Administrator creation

```bash
python manage.py createsuperuser --settings=config.settings.prod
```

## HTTPS and domain configuration

- point the domain to the server
- configure `ALLOWED_HOSTS` to include the live domain
- configure `CSRF_TRUSTED_ORIGINS` for the browser origin
- enable your TLS certificate
- leave `SECURE_SSL_REDIRECT=True` in production

## Backup and restore

- create a PostgreSQL dump before updates
- keep application configuration files in version control or secure backup storage
- test restore procedures before production go-live

## Rollback

1. restore the database from the latest backup
2. redeploy the previous application version
3. rerun migration checks if needed
4. verify queue operations and admin login
