# QueueSystem v1.0.0

This package contains the customer-facing installation bundle for the QueueSystem queue management solution. It is intended for a licensed self-hosted deployment and includes the core installation, deployment, documentation, and operational files required for a professional customer rollout.

## Package structure

- application/ — application source and deployment notes
- deployment/ — infrastructure, installation, and restore instructions
- documentation/ — customer-facing admin, operations, and technical references
- scripts/ — installation and maintenance scripts
- .env.example — environment variables template
- CHANGELOG.md — product changes for the v1.0 release
- LICENSE.txt — commercial license text for the licensed deployment

## Release version

- Version: v1.0.0
- Status: commercial baseline
- Intended deployment: self-hosted production environment

## Supported deployment model

QueueSystem v1.0.0 is intended for:

- Linux-based hosting
- PostgreSQL 16+
- Python 3.12+
- HTTPS-enabled public domain
- self-hosted or managed deployment

## Customer obligations

The customer must:

- provide a supported server environment
- provide database access
- configure DNS and TLS
- maintain secure environment variables
- maintain regular backups
- appoint a system administrator

## Important note

This package is a deployment bundle and is intended to be used under the terms of the included commercial license agreement. Do not redistribute or publish the source code without authorisation.
