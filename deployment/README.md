# Queue System Deployment Guide

## Supported environments

This project is designed for a Linux-based production deployment using:

- Python 3.12+
- PostgreSQL 16+
- Nginx or a reverse proxy for HTTPS termination
- A managed or self-hosted PostgreSQL instance

## Minimum requirements

- 2 vCPU
- 4 GB RAM
- 20 GB SSD storage
- static public IP or valid domain
- HTTPS certificate
- PostgreSQL database with network access from the application server

## Environment variables

Copy [.env.example](../.env.example) to `.env` and fill in the required values.

Required values:

- `SECRET_KEY`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL` or PostgreSQL variables
- `KIOSK_API_KEY`
- `DEBUG=False`

### Vercel deployment

Vercel does not import `.env.example`. Add the production values in the Vercel project settings or with the Vercel CLI before deploying. At minimum, configure `SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and `KIOSK_API_KEY` for the Production environment. Use a unique randomly generated `SECRET_KEY` and never commit it to Git.

Example CLI setup (the secret values are entered interactively or supplied from a secure secret manager):

```bash
vercel env add SECRET_KEY production
vercel env add DATABASE_URL production
vercel env add ALLOWED_HOSTS production
vercel env add CSRF_TRUSTED_ORIGINS production
vercel env add KIOSK_API_KEY production
vercel --prod
```

The repository's `vercel.json` sets `DJANGO_SETTINGS_MODULE=config.settings.prod` and `VERCEL=1`. PostgreSQL must be reachable from Vercel; a private Docker hostname such as `db` will not work from a Vercel function. If the database is private, use a supported public or serverless PostgreSQL endpoint with TLS, or deploy QueueSystem on the documented VM or Docker model instead.

## One-time setup

1. Create a PostgreSQL database.
2. Create a dedicated application database user.
3. Configure your environment file.
4. Install dependencies:
   `pip install -r requirements.txt`
5. Run migrations:
   `python manage.py migrate --settings=config.settings.prod`
6. Collect static files:
   `python manage.py collectstatic --noinput --settings=config.settings.prod`
7. Create an administrator:
   `python manage.py createsuperuser --settings=config.settings.prod`

## Production launch

Use a process manager such as systemd or Docker Compose.

Example:

```bash
python manage.py runserver 0.0.0.0:8000 --settings=config.settings.prod
```

For repeatable, production-style deployments, the repository includes a Docker configuration and a bootstrap script.

## HTTPS and domain configuration

- Configure the domain to point to the application server.
- Set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` to your production hosts.
- Enable TLS termination via Nginx, Caddy, or a cloud load balancer.
- Keep `SECURE_SSL_REDIRECT=True` in production.

## Backup and restore

### Backup

```bash
pg_dump --format=custom --file=queue_system_backup.dump queue_system
```

### Restore

```bash
pg_restore --clean --if-exists --dbname=queue_system queue_system_backup.dump
```

## Rollback

1. Restore the database backup.
2. Re-deploy the prior application build.
3. Re-run migrations if the version requires them.
4. Confirm static files and admin access are working.

## Production checklist

- [ ] `DEBUG=False`
- [ ] `SECRET_KEY` configured and unique
- [ ] `ALLOWED_HOSTS` set to production hosts
- [ ] `CSRF_TRUSTED_ORIGINS` set for the real domain
- [ ] PostgreSQL selected, not SQLite
- [ ] `KIOSK_API_KEY` set
- [ ] HTTPS enabled
- [ ] Admin user created
- [ ] Backups scheduled
- [ ] Monitoring configured
