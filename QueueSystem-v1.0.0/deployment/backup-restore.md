# Backup and Restore Procedure

## Backup

Use PostgreSQL logical or file-based backups before any major update.

```bash
pg_dump --format=custom --file=queue_system_backup.dump queue_system
```

Also back up:

- `.env`
- reverse proxy configuration
- TLS certificates
- static asset directories

## Restore

```bash
pg_restore --clean --if-exists --dbname=queue_system queue_system_backup.dump
```

## Rollback checklist

- confirm the database restore succeeded
- redeploy the previous application build
- validate the environment file matches the live deployment
- run the application health check
- test one queue transaction and an admin login
