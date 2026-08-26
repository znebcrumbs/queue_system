# Change Log

QueueSystem follows Semantic Versioning: `MAJOR.MINOR.PATCH`. Major versions may contain breaking changes, minor versions add backwards-compatible functionality, and patch versions contain backwards-compatible fixes.

Release notes use the headings Added, Changed, Fixed, Security, Deprecated, Removed, Breaking changes, and Upgrade notes. Database schema changes are documented with the release and must be applied using Django migrations.

## v1.0.0

### Added
- queue ticketing workflow for service-based customer flow
- administrator and staff role management
- queue dashboard controls and operational status views
- kiosk and ticket generation flow
- basic reporting and monitoring interfaces
- production security configuration template
- repeatable deployment package and installation documentation

### Improved
- hardened production defaults for HTTPS and secure cookies
- PostgreSQL-first deployment configuration
- clearer deployment and environment variable structure
- customer-facing installation and operations documentation

### Fixed
- production security defaults tightened
- deployment readiness improved for customer rollout
- repository hygiene improved for local secrets and artifacts

### Known limitations
- not yet a full SaaS multi-tenant product
- no white-label reseller edition in this release
- no SMS or email notification automation in the baseline bundle
- custom integrations are outside the core v1.0 scope
