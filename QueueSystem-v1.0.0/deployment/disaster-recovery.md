# Disaster Recovery Guide

## Recovery objectives

Agree a recovery time objective (RTO) and recovery point objective (RPO) with the customer before go-live. The default operating procedure is a daily database backup, a weekly retained backup, and an off-host encrypted copy.

## Daily and weekly SOP

Daily: create a PostgreSQL custom-format dump, encrypt it, upload it to restricted backup storage, and record success and size. Weekly: test a restore into an isolated database, verify a login and representative queue records, and retain the result with the backup inventory. Never overwrite the only known-good backup.

## Restore procedure

1. Declare the incident and record the last known-good backup.
2. Provision a clean host with the supported runtime and restricted network access.
3. Deploy the matching QueueSystem release and restore the protected `.env` values.
4. Restore PostgreSQL into a new database, validate ownership and permissions, then run migrations only when the release requires them.
5. Start the application, verify HTTPS, login, kiosk, counter, and reporting workflows.
6. Update DNS only after validation, then monitor logs and queue activity.

## Accidental deletion or migration failure

Stop writes where possible, preserve logs, and restore the most recent pre-incident backup into a separate database. Compare the affected records, obtain customer approval, and switch over only after acceptance. For a failed migration, follow the rollback section in `upgrade-guide.md`; do not manually delete migration history.

## Recovery record

Record incident date, release, backup identifier, restore operator, restore result, data-loss window, customer approval, and follow-up actions.