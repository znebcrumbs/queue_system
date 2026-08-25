# Queue System Commercial Readiness Status

## Executive summary

This project is in a strong technical prototype state, but it is not yet in a customer-ready commercial state. The codebase already contains a substantial amount of work in security, deployment, and product planning, but the final commercial gate still requires a controlled freeze, cleanup, and packaging around a verified v1.0 release.

The strongest evidence of readiness is the presence of structured configuration for Django production settings, environment variables, security hardening, and phase-based documentation across the repository. The main blockers are still the same ones you flagged earlier: secrets and local development artifacts remain in the repository, production configuration still allows SQLite fallback, and the repo still lacks the commercial packaging, support terms, license, and customer-facing documentation required for a sale.

## Current repo assessment

### What is already in place

- Production settings scaffolding exists in [config/settings/prod.py](config/settings/prod.py)
- Environment template exists in [.env.example](.env.example)
- Security headers and hardening logic are present in [config/settings/base.py](config/settings/base.py)
- The project already has a substantial documentation set, including phase reports and operational checklists
- A production deployment path is at least partially documented and prepared

### Critical blockers before commercial sale

1. Secret material is still present in the repo
   - The tracked environment file [.env](.env) contains live values
   - The default secret key in [config/settings/base.py](config/settings/base.py) is still a fallback insecure development key
   - This should never be part of a customer-facing or shared repository

2. Production mode still permits SQLite as a fallback
   - [config/settings/prod.py](config/settings/prod.py) includes an SQLite fallback when PostgreSQL is not configured
   - That is acceptable for local testing, but not for a commercial production baseline

3. Customer-facing packaging is not complete
   - No commercial license agreement is included
   - No installation package layout is present for adoption by a customer IT team
   - No operations or admin handover package exists in a customer-ready bundle

4. Documentation is not yet packaged as a supported customer experience
   - The repo has separate planning notes, but it does not yet provide a clean, single source of truth for installation, operations, training, and support

5. Fresh-install verification is still a requirement, not a claim
   - The app may be operational locally, but a clean installation, migration, and admin setup still need to be validated as a formal release gate

---

## Phase-by-phase readiness

### Phase 0 — Freeze the current product
Status: Partial

Required actions:
- Tag the current working version as v1.0.0-beta
- Record the current feature set from the codebase and docs
- Confirm the production deployment path works from a clean environment
- Confirm migrations work from a clean database
- Confirm a fresh installation can be created
- Document the known bugs and deferred items
- Decide which features are officially included in v1.0
- Freeze new feature work until the baseline is stable

Recommendation:
- Establish a signed-off v1.0 scope before adding anything new
- Treat this as the first release gate, not a “it mostly works” milestone

### Phase 1 — Security and production hardening
Status: Partial

Already covered:
- Security middleware is present
- CSRF and session settings are in place
- HTTPS and HSTS configuration exists
- Clickjacking and XSS protections are configured

Still required:
- Review every protected endpoint for RBAC enforcement
- Audit all role permission checks for cross-tenant and cross-org leakage
- Remove all embedded credentials and local secret values
- Make sure production settings are truly enforced by environment, not just defaults
- Resolve any default-secret fallback in the settings layer

### Phase 2 — Make deployment repeatable
Status: Partial

Already covered:
- Environment configuration exists
- A production configuration pattern exists
- The repo contains deployment-related notes and setup references

Still required:
- Create a clean, customer-facing installation guide
- Document supported hosting environments and requirements
- Document admin creation, migrations, static file collection, backups, and restores
- Define production database requirements clearly and enforce PostgreSQL-only production configuration
- Build a clean installation checklist that can be followed without custom troubleshooting

### Phase 3 — Create a proper installation package
Status: Not yet complete

Required customer package structure:
- application/
- deployment/
- documentation/
- scripts/
- .env.example
- CHANGELOG.md
- LICENSE.txt

Current gap:
- The codebase is still effectively a repository, not a packaged commercial installation bundle

### Phase 4 — Build the customer documentation
Status: Incomplete

It needs all of the following as formal customer-facing documentation:
- Installation guide
- Administrator manual
- Operations manual
- Technical reference

This is a commercial requirement, not just internal engineering documentation

### Phase 5 — Create onboarding and training
Status: Not started

Required:
- Administrator training plan
- Staff training plan
- Handover checklist
- Acceptance record

### Phase 6 — Make deployment configurable
Status: Partial

The app already supports configurable environment values, but customer-specific branding and operational settings still need a formal configuration model for real-world deployments.

### Phase 7 — Production testing
Status: Partial

Required formal release testing:
- Authentication
- RBAC
- Queue operations
- Display behavior
- Administration functions
- Failure mode testing

### Phase 8 — Deployment package for the “I’ll set it up” offer
Status: Not started

There should be a deployment SOP for internal setup work and repeatable customer onboarding.

### Phase 9 — Commercial licensing
Status: Not started

This is non-negotiable for a real commercial offer. A lawyer-reviewed commercial license is required before selling to businesses.

### Phase 10 — Pricing structure
Status: Not started

Required:
- self-hosted pricing
- managed deployment pricing
- maintenance pricing
- custom development pricing

### Phase 11 — Customer-facing sales material
Status: Not started

Required:
- professional landing page
- feature overview
- pricing
- screenshots
- demo credentials
- FAQ
- booking/contact flow

### Phase 12 — Australian-specific readiness
Status: Partial

The product is conceptually relevant to Australian customers, but customer-facing legal and operational documentation still needs to be aligned with Australian business contract requirements.

### Phase 13 — Maintenance infrastructure
Status: Not started

Required:
- version tracking
- release process
- rollback and backup procedures
- support process
- maintenance schedule

### Phase 14 — Customer lifecycle process
Status: Not started

This must be formalized as a sales-to-handover workflow, not just product delivery.

### Phase 15 — Internal sales assets
Status: Not started

Required:
- one-page product sheet
- proposal template
- pricing sheet
- SOW template
- commercial license agreement
- maintenance agreement
- discovery questionnaire
- onboarding checklist
- handover form

---

## Recommended release order

### P0 — must do before selling
1. Remove secrets and local-only files from the repo
2. Audit production config and eliminate SQLite fallback for production
3. Freeze the scope and tag v1.0.0-beta
4. Perform fresh-install validation from a clean environment
5. Complete customer installation documentation
6. Establish backup and restore procedures
7. Prepare a commercial license agreement
8. Create support terms and maintenance terms

### P1 — required to make it worth serious money
1. Customer-configurable branding
2. Customer-configurable services and counters
3. Repeatable deployment SOP
4. Training program and handover package
5. Professional demo and proposal material

### P2 — makes the business scalable
1. Docker deployment
2. Automated deployment scripts
3. Monitoring and health-checking
4. Update and rollback automation
5. Customer version tracking

### P3 — future upsells
1. QR queue tracking
2. SMS/email notifications
3. API integrations
4. multi-branch support
5. white-label and reseller edition

---

## The immediate action plan

### Next 7 days
- Remove or clean all live secret material from the repo and treat [.env](.env) as local-only
- Make PostgreSQL the production-only database requirement in the settings and deployment docs
- Freeze the product scope and create the v1.0.0-beta tag
- Validate a clean database migration and fresh installation test
- Draft a single installation and deployment guide for a customer IT operator

### Next 30 days
- Build the customer package directory structure
- Write admin/operations/technical documentation
- Create training materials and handover checklist
- Prepare pricing, proposal, and support documents
- Obtain legal review for commercial licensing and customer terms

---

## Bottom line

The project is technically close to a viable queue management product, but it is not yet a commercial-grade release package. The right move is not a major rewrite; it is a disciplined commercial baseline:

- freeze the feature set
- harden the production configuration
- clean the repo
- verify fresh install and migration behavior
- package the support documentation
- put the commercial terms in place

That is the bridge from a working project to something you can confidently sell as a licensed product.
