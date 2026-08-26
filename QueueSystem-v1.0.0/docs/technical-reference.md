# Technical Reference

## Architecture

QueueSystem is a Django-based queue management application designed for service-based customer flow and staff operations. It supports administrator dashboards, queue operations, kiosk interfaces, and reporting.

## Technology stack

- Django 5.x
- PostgreSQL 16+
- Python 3.12+
- Django REST Framework
- Redis and Channels for event support where enabled
- Nginx or equivalent reverse proxy for production hosting

## Database model overview

The application uses PostgreSQL for production and stores queue configuration, service definitions, counters, tickets, and user metadata. Production deployments should not rely on SQLite.

## Environment variables

Important variables include:

- `DEBUG`
- `SECRET_KEY`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `KIOSK_API_KEY`

## Authentication and authorization

The application uses the Django authentication system with application-level checks for role-based access and operational permissions. All protected endpoints should be reviewed for RBAC enforcement before customer deployment.

## Roles and responsibilities

Typical roles:

- Administrator: full configuration and system control
- Manager or supervisor: workflow oversight and operational review
- Staff: service handling and ticket calls
- kiosk user: customer queue initiation and service access

## Deployment model

The production deployment is expected to use:

- PostgreSQL database
- HTTPS front-end
- dedicated environment variables
- reverse proxy and TLS termination
- secure static file collection before launch

## Logging

Review application logs for:

- failed login attempts
- queue operations
- permission errors
- database connection issues
- application exceptions

## Backup and restore

Perform regular database backups, and maintain the environment file and reverse-proxy config as part of the backup process.

## Security

Production security controls should include:

- `DEBUG=False`
- strong `SECRET_KEY`
- explicit `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- HTTPS redirection
- secure cookies
- HSTS enforcement
- no SQLite in production

## Troubleshooting

### System does not start

Check:

- environment variables
- database connectivity
- Python virtual environment
- static file collection

### Queue actions failing

Verify:

- staff permissions
- service configuration
- queue state
- database connectivity

### Login issues

Check:

- correct role assignment
- password reset flow
- user account status
- domain and HTTPS configuration
