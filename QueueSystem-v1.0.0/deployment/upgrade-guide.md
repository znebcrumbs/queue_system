# Upgrade and Migration Guide

## Version policy

QueueSystem uses Semantic Versioning. Read the target release notes before every upgrade. Never skip a required migration or run an application version against an unverified database backup.

## Standard upgrade

1. Record the current version and maintenance window.
2. Notify staff and stop new kiosk activity.
3. Take and verify a PostgreSQL backup. Keep the current `.env` outside the release directory.
4. Deploy the new application files to a new versioned directory.
5. Install the pinned dependencies from `requirements.txt`.
6. Run `python manage.py migrate --settings=config.settings.prod`.
7. Run `python manage.py collectstatic --noinput --settings=config.settings.prod`.
8. Restart the application process and reverse proxy if required.
9. Verify administrator login, kiosk ticket creation, counter actions, and reporting.
10. Record the completed version and migration result.

## Database migration guide

Migrations are forward-only application changes. Run them from the release directory using the production settings. Inspect the migration plan first with `python manage.py showmigrations --settings=config.settings.prod`, then apply it with `python manage.py migrate --settings=config.settings.prod`. Do not edit applied migration files. Test restores and migrations against a staging copy before a major upgrade.

## Rollback

If the application fails validation, stop the service, restore the previous application directory, and restore the database backup when the migration changed schema or data. Restart the previous version and verify queue operations. Preserve logs and the migration output for support.

## Breaking changes

The v1.0.0 baseline has no earlier supported upgrade path. Future releases must list incompatible configuration, API, database, browser, or deployment changes under a `Breaking changes` heading and provide a migration action.