# QueueSystem

QueueSystem is a self-hosted queue management platform for service organisations. It brings ticketing, counters, staff roles, service configuration, operational monitoring, audit history, and customer feedback into one focused workflow.

## Why QueueSystem

- Keep customer flow visible from ticket creation to service completion.
- Give administrators controlled configuration for departments, services, counters, and staff.
- Support auditable operations with role-based access and activity history.
- Deploy on infrastructure you control with PostgreSQL and HTTPS.

## Feature matrix

| Capability | Included |
| --- | --- |
| Service and department queues | Yes |
| Kiosk ticket generation | Yes |
| Counter and staff workflow | Yes |
| Role-based administration | Yes |
| Audit logging | Yes |
| Customer surveys and ratings | Yes |
| Basic operational reporting | Yes |
| SMS/email notifications | Not in v1.0.0 |
| SaaS multi-tenancy | Not in v1.0.0 |

## Deployment

The supported baseline is Ubuntu or Debian, Python 3.12+, PostgreSQL 16+, and an HTTPS reverse proxy. Docker Compose and Windows Server are documented as deployment options. See [QueueSystem-v1.0.0/README.md](QueueSystem-v1.0.0/README.md) for the customer package and [QueueSystem-v1.0.0/deployment/README.md](QueueSystem-v1.0.0/deployment/README.md) for installation.

## Documentation

- [Installation guide](QueueSystem-v1.0.0/docs/installation-guide.md)
- [Administrator manual](QueueSystem-v1.0.0/docs/administrator-manual.md)
- [Operations manual](QueueSystem-v1.0.0/docs/operations-manual.md)
- [Security guide](QueueSystem-v1.0.0/deployment/security-guide.md)
- [Disaster recovery guide](QueueSystem-v1.0.0/deployment/disaster-recovery.md)
- [Upgrade guide](QueueSystem-v1.0.0/deployment/upgrade-guide.md)

## Licensing and support

QueueSystem is licensed for self-hosted use under [LICENSE.txt](QueueSystem-v1.0.0/LICENSE.txt). Evaluation credentials and support contacts are issued per customer environment. Deployment and maintenance services are available under separate agreements.

## Version

Current release: **v1.0.0**. Versioning follows Semantic Versioning; release notes and breaking changes are recorded in [CHANGELOG.md](QueueSystem-v1.0.0/CHANGELOG.md).
