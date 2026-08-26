# QueueSystem v1.0.0

QueueSystem is a self-hosted queue management system for organisations that need a clear, auditable customer-flow process across services, counters, staff, and departments. This release is the production baseline for licensed deployments.

## Package structure

- app/ — application source and runtime notes
- deployment/ — installation, infrastructure, security, backup, and recovery guides
- docs/ — administrator, operations, and technical references
- CHANGELOG.md — product changes for the v1.0 release
- LICENSE.txt — commercial license text for the licensed deployment

Internal engineering, QA, sales, and phase documents are maintained outside this customer package in the repository's `internal-docs/` directory.

## Release version

- Version: v1.0.0
- Status: commercial baseline
- Intended deployment: self-hosted production environment

## Core capabilities

| Area | Included in v1.0.0 |
| --- | --- |
| Queue operations | Ticket generation, service queues, counter workflows, status controls |
| Administration | Department, service, counter, user, and role management |
| Monitoring | Operational dashboard, queue status, and basic reporting |
| Feedback | Post-service survey and rating workflow |
| Security | Role-based access, audit logging, HTTPS-ready production settings |

## Supported deployment model

QueueSystem v1.0.0 is intended for:

- Linux-based hosting
- PostgreSQL 16+
- Python 3.12+
- HTTPS-enabled public domain
- self-hosted or managed deployment

## Deployment options

- Ubuntu or Debian with Gunicorn and Nginx
- Docker Compose for repeatable installation
- PostgreSQL 16 or later as the production database
- Windows Server using a Python virtual environment and a reverse proxy

Start with [deployment/README.md](deployment/README.md), then use [docs/installation-guide.md](docs/installation-guide.md).

## Documentation

- [Administrator manual](docs/administrator-manual.md)
- [Operations manual](docs/operations-manual.md)
- [Technical installation guide](docs/installation-guide.md)
- [Security guide](deployment/security-guide.md)
- [Disaster recovery guide](deployment/disaster-recovery.md)
- [Upgrade and migration guide](deployment/upgrade-guide.md)

## Demo access

Demo credentials are provided separately by the licensor for each evaluation or customer environment. Do not deploy shared demo credentials to production. After installation, create a named administrator and remove any temporary account.

## Customer obligations

The customer must:

- provide a supported server environment
- provide database access
- configure DNS and TLS
- maintain secure environment variables
- maintain regular backups
- appoint a system administrator

## License

This package is supplied under the included commercial license agreement. Review [LICENSE.txt](LICENSE.txt) before deployment. Version upgrades, support, and optional deployment services are governed by the customer agreement.
