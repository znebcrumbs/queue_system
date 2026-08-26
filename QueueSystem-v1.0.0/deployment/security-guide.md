# Infrastructure Security Guide

## Network controls

- Expose only TCP 80 and 443 publicly; restrict SSH to trusted administrator addresses.
- Keep PostgreSQL on a private interface or Docker network. Never publish port 5432 to the internet.
- Isolate the application, database, and reverse proxy networks where the deployment platform supports it.
- Use a host firewall and review rules after every infrastructure change.

## TLS and reverse proxy

Use a current TLS certificate, redirect HTTP to HTTPS, enable HSTS only after HTTPS is confirmed, and forward the original protocol and host headers correctly. Configure security headers in Nginx or Apache, including `X-Content-Type-Options`, `Referrer-Policy`, and an appropriate `Content-Security-Policy` after testing the application.

## Secrets and access

Keep `.env`, database passwords, API keys, and signing secrets out of source control and backups that are broadly accessible. Rotate secrets after staff changes, suspected exposure, or provider changes. Use named administrator accounts, least privilege, MFA on the hosting provider, SSH keys rather than passwords, and automatic security updates.

## Host and container hardening

Disable password SSH login and root SSH login, restrict sudo, and consider Fail2ban for SSH and reverse-proxy abuse. Run containers as non-root where supported, use pinned images, remove unused capabilities, and avoid mounting the Docker socket into application containers.

## Backups and logs

Encrypt backups in transit and at rest, restrict backup access, and test restoration regularly. Retain application, reverse-proxy, authentication, and database logs according to the customer retention policy. Do not log passwords, tokens, or full secrets.

## Verification checklist

- [ ] TLS certificate and renewal verified
- [ ] Firewall ports reviewed
- [ ] PostgreSQL is not publicly reachable
- [ ] Secrets are outside source control
- [ ] SSH hardening completed
- [ ] Security headers reviewed
- [ ] Backup encryption and retention confirmed