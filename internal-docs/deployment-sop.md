# Deployment SOP

## Customer questionnaire

- Customer name, site, timezone, operating hours, and go-live date
- Public domain, DNS owner, hosting provider, and support contacts
- Expected daily volume, departments, services, counters, and staff count
- Data retention, backup, RTO, RPO, and integration requirements

## Infrastructure checklist

- [ ] Supported server and PostgreSQL provisioned
- [ ] OS patched and firewall configured
- [ ] SSH access restricted and logged
- [ ] Application, database, and backup storage allocated
- [ ] DNS record created and TLS certificate available

## Application checklist

- [ ] Production environment variables supplied securely
- [ ] Database user has least required privileges
- [ ] Migrations and static files completed
- [ ] Initial administrator created with named account
- [ ] Branding, departments, services, counters, and staff configured
- [ ] Queue, kiosk, counter, survey, and role permissions tested

## Acceptance and handover

- [ ] Customer acceptance test completed
- [ ] Backup and restore test recorded
- [ ] Monitoring and log retention confirmed
- [ ] Version and license recorded
- [ ] Handover package delivered
- [ ] Maintenance and escalation contact confirmed