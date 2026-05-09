# 🚀 QUEUE SYSTEM - COMPLETE REFACTOR ROADMAP

**Last Updated:** April 9, 2026  
**Project Status:** Foundation Complete ✅ | Ready for PHASE 2 → PHASE 3

---

## 📊 CURRENT STATE

### ✅ PHASE 1 — FOUNDATION (100% COMPLETE)

**All structural requirements met:**

| Requirement | Status | Details |
|-------------|--------|---------|
| Apps in `/apps/` | ✅ | accounts, queues, survey |
| Config split | ✅ | base.py, dev.py, prod.py |
| Import convention | ✅ | All using `apps.accounts`, etc. |
| `.gitignore` | ✅ | Exists |
| `.env` setup | ✅ | Both `.env` and `.env.example` |
| `python-decouple` | ✅ | Loading all config from env vars |
| INSTALLED_APPS | ✅ | Correct configuration |
| WSGi/ASGI | ✅ | Properly configured |
| Database support | ✅ | PostgreSQL + SQLite |

**No breaking changes needed.** System is ready for Phase 2.

---

## 🔴 PHASE 2 — CRITICAL SECURITY (NEXT - DO THIS NOW!)

### ⏱️ Time Estimate: **30-60 minutes**

### What to do:
1. Read: [PHASE_2_SECURITY_SETUP.md](./PHASE_2_SECURITY_SETUP.md) (in project root)
2. Update 3 settings files with exact code provided
3. Test locally with DEBUG=False
4. Verify environment variables

### Key Changes:
- ✅ Add security headers (X-Frame-Options, etc.)
- ✅ Implement secure cookies for production
- ✅ Proper CSRF_TRUSTED_ORIGINS per environment
- ✅ Set DEBUG=False in production by default
- ✅ Enforce HTTPS/SSL settings

### Files to Modify:
```
config/settings/base.py      (ADD security headers)
config/settings/dev.py        (REPLACE with new config)
config/settings/prod.py       (REPLACE with new config)
.env.example                  (UPDATED ✅)
.env                          (UPDATED ✅)
```

### Security Checklist:
- [ ] Updated base.py with headers
- [ ] Updated dev.py with dev settings  
- [ ] Updated prod.py with prod settings
- [ ] Config is environment-variable driven
- [ ] Tested locally with DEBUG=False
- [ ] Ran `python manage.py check --deploy`
- [ ] All @csrf_exempt endpoints verified (✅ Already secure)
- [ ] All authenticated endpoints have @login_required (✅ Verified)

---

## 🧠 PHASE 3 — SYSTEM DESIGN (AFTER PHASE 2)

### ⏱️ Time Estimate: **2-3 days**

### What to do:
1. Read: [PHASE_3_SYSTEM_DESIGN.md](./PHASE_3_SYSTEM_DESIGN.md) (in project root)
2. Follow 7 implementation steps in order
3. Create migrations and run them
4. Test each step before continuing

### Key Features to Add:

#### 3A - Organization Model
- Multi-tenant backbone
- Users, Departments, Tickets belong to org
- **Before:** App handles single organization implicitly
- **After:** Full multi-org support

#### 3B - Ticket Model (Base Entity)
- Replaces QueueEntry with flexible ticket system
- Support multiple ticket types (SERVICE, COMPLAINT, INQUIRY, etc.)
- Track wait time and resolution time automatically
- **Before:** Only queue entries (single use case)
- **After:** Universal ticket abstraction

#### 3C - RBAC (Role-Based Access Control)
- Define strict permissions per role
- ADMIN, REGISTRAR, MIS have different capabilities
- Enforce in views with decorators
- **Before:** Roles existed but not enforced
- **After:** Permissions strictly enforced

#### 3D - Audit Logging
- Track all changes (who, what, when, where)
- Automatic signal-based logging
- Complete trail for compliance
- **Before:** No audit trail
- **After:** Full audit trail

### Implementation Order:
1. Create `Organization` model
2. Create `Ticket` model
3. Create `apps/audit` app
4. Create `AuditLog` model + signals
5. Create RBAC decorators
6. Update views to use RBAC
7. Run migrations & test

---

## 📁 PROJECT STRUCTURE (AFTER ALL PHASES)

```
queue_system/
├── .env                              # Actual secrets (NEVER commit)
├── .env.example                      # Template (commit this)
├── .gitignore                        # ✅ Exists
├── PHASE_2_SECURITY_SETUP.md        # New - Security guide
├── PHASE_3_SYSTEM_DESIGN.md         # New - Architecture guide
├── CODEBASE_DOCUMENTATION.txt       # Updated with current state
│
├── manage.py                         # Django CLI
├── requirements.txt                  # Dependencies
│
├── config/
│   ├── __init__.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── settings/
│       ├── __init__.py
│       ├── base.py         (PHASE 2: ADD security headers)
│       ├── dev.py          (PHASE 2: UPDATE)
│       └── prod.py         (PHASE 2: UPDATE)
│
├── apps/
│   ├── accounts/           # User authentication & roles
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── decorators.py   (PHASE 3: NEW - RBAC decorators)
│   │   └── permissions.py  (PHASE 3: NEW - Permission logic)
│   │
│   ├── queues/             # Core queue/ticket system
│   │   ├── models.py       (PHASE 3: ADD Organization + Ticket)
│   │   ├── views.py        (PHASE 3: ADD RBAC decorators)
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── management/
│   │       └── commands/
│   │           └── seed_data.py
│   │
│   ├── survey/             # Customer feedback/survey
│   │   ├── models.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   └── audit/              # PHASE 3: NEW - Audit trail
│       ├── __init__.py
│       ├── models.py       # AuditLog model
│       ├── signals.py      # Auto-logging signals
│       ├── apps.py
│       └── views.py        # Audit reporting
│
├── templates/              # HTML templates
│   ├── accounts/
│   ├── q_queues/
│   ├── q_survey/
│   └── layouts/
│
└── logs/                   # (created at runtime)
    └── queue_system.log
```

---

## 🎯 PRIORITY & TIMELINE

### This Week (PHASE 2) - **CRITICAL**
```
Monday:   Review PHASE_2_SECURITY_SETUP.md
Tuesday:  Implement security settings (30 min)
Tuesday:  Test locally with DEBUG=False (15 min)
Tuesday:  Run Django security check (5 min)
Wednesday: Deploy to staging if applicable
```

**Why:** Security debt is the highest priority. 
- @csrf_exempt endpoints need HTTPS
- DEBUG=False must be enforced in prod
- SECRET_KEY must never be hardcoded
- Database credentials must be environment variables

### Next Week (PHASE 3) - **ARCHITECTURE**
```
Monday-Tuesday: Create Organization model
Tuesday-Wednesday: Create Ticket model + migration
Wednesday: Implement RBAC decorators
Thursday: Update views with RBAC
Friday: Create audit system + signals
Friday: Full system test
```

**Why:** Enterprise features unlock:
- Multi-organization support
- Complete audit trail for compliance
- Flexible ticket system for growth
- Strict access control for security

---

## ✅ PHASE 2 QUICK START

### 1. Read the guide (10 min):
```powershell
# Open PHASE_2_SECURITY_SETUP.md in your editor
notepad PHASE_2_SECURITY_SETUP.md
```

### 2. Update config/settings/base.py:
- Copy the security headers section
- Paste at the END of base.py
- Save

### 3. Update config/settings/dev.py:
- Replace entire file with version from guide
- Save

### 4. Update config/settings/prod.py:
- Replace entire file with version from guide
- Save

### 5. Test:
```powershell
# Test with dev settings
python manage.py runserver --settings=config.settings.dev

# Test with prod settings
$env:DEBUG="False"
python manage.py runserver --settings=config.settings.prod --nothreading

# Run security check
python manage.py check --deploy --settings=config.settings.prod
```

### 6. Verify:
- [ ] No errors with DEBUG=False
- [ ] Security check passes
- [ ] All endpoints still work
- [ ] Static files load correctly

---

## 📚 REFERENCE DOCUMENTS (IN PROJECT ROOT)

| File | Purpose | Read When |
|------|---------|-----------|
| [CODEBASE_DOCUMENTATION.txt](./CODEBASE_DOCUMENTATION.txt) | Overall system docs | Getting oriented |
| [PHASE_2_SECURITY_SETUP.md](./PHASE_2_SECURITY_SETUP.md) | Security implementation | Before PHASE 2 |
| [PHASE_3_SYSTEM_DESIGN.md](./PHASE_3_SYSTEM_DESIGN.md) | Architecture & models | Before PHASE 3 |
| [.env.example](./.env.example) | Config template | Setting up new env |
| [requirements.txt](./requirements.txt) | Dependencies | Installing packages |

---

## 🔗 IMPORTANT ENDPOINTS

### Current (Work)
- `/admin/` - Django admin
- `/login/` - Staff login
- `/queues/` - Queue management (staff)
- `/accounts/` - User management

### Kiosk (Protected by API key)
- `POST /queues/create_queue_entry/` - Create ticket (KIOSK_API_KEY required)
- `POST /queues/update_queue_entry/<id>/` - Update status (API key or auth)
- `GET /queues/generate_qr/<id>/` - Get QR code

### Reports
- `/queues/reports_dashboard/` - Analytics
- `/queues/export_queues_csv/` - Export data

---

## 🚨 CRITICAL REMINDERS

### For PHASE 2:
- ⚠️ **NEVER hardcode SECRET_KEY** - Always use .env
- ⚠️ **DEBUG=False in production** - Non-negotiable
- ⚠️ **HTTPS only** - Use SECURE_SSL_REDIRECT=True
- ⚠️ **Secure cookies** - SESSION_COOKIE_SECURE=True in prod
- ⚠️ **API key protection** - KIOSK_API_KEY must be strong & random

### For PHASE 3:
- ⚠️ **Test migrations** - Always test on staging first
- ⚠️ **Data backup** - Backup before data migration
- ⚠️ **Gradual rollout** - Don't deploy all at once
- ⚠️ **User testing** - Have staff test RBAC permissions

---

## 📞 TROUBLESHOOTING

### "DEBUG=False and static files not loading"
```powershell
python manage.py collectstatic --settings=config.settings.prod --no-input
```

### "CSRF token missing"
- Check `CSRF_TRUSTED_ORIGINS` in settings
- Ensure `@csrf_exempt` endpoints have API key validation
- Verify cookies are being set

### "AttributeError: module 'config' has no attribute 'settings'"
- Check DJANGO_SETTINGS_MODULE is correct
- Ensure config/settings/dev.py exists
- Run: `python manage.py --help` to verify

### "Unauthorized access to kiosk endpoint"
- Verify KIOSK_API_KEY is set in .env
- Check header: `X-KIOSK-API-KEY: <your-key>`
- Check logs for exact error message

---

## 📊 SUCCESS METRICS

### After PHASE 2:
- ✅ Django security check passes
- ✅ DEBUG=False works locally
- ✅ All endpoints respond correctly
- ✅ No error logs for missing settings

### After PHASE 3:
- ✅ Organization model working
- ✅ Ticket model replacing QueueEntry
- ✅ RBAC enforced in all views
- ✅ Audit logs recording all changes
- ✅ No permission bypass vulnerabilities

---

## 🎓 KNOWLEDGE BASE

### Django Security Best Practices:
- [Django Security Documentation](https://docs.djangoproject.com/en/5.2/topics/security/)
- OWASP Top 10 for web applications
- CWE (Common Weakness Enumeration)

### Environment Management:
- [python-decouple docs](https://pypi.org/project/python-decouple/)
- 12 Factor App methodology
- Never commit .env file

### RBAC Pattern:
- Role-based access control principles
- Decorator pattern in Python
- Django permission system

---

## ✨ NEXT ACTIONS

### Immediate (Today):
1. ✅ Read this roadmap completely
2. ✅ Check PHASE_2_SECURITY_SETUP.md
3. ✅ Have Phase 2 implementation ready

### This Week:
1. 🔴 Implement PHASE 2 security changes
2. 🔴 Test thoroughly with DEBUG=False
3. 🔴 Verify all endpoints work
4. 🔴 Run `python manage.py check --deploy`

### Next Week:
1. 🟡 Start PHASE 3 implementation
2. 🟡 Create Organization & Ticket models
3. 🟡 Implement RBAC system
4. 🟡 Add audit logging

### Success:
1. 🟢 Production-ready codebase
2. 🟢 Enterprise-grade security
3. 🟢 Scalable multi-org architecture
4. 🟢 Complete audit trail
5. 🟢 Role-based access control

---

## 📋 QUICK REFERENCE - COMMANDS

```powershell
# Run with specific settings
python manage.py runserver --settings=config.settings.dev
python manage.py runserver --settings=config.settings.prod

# Security check
python manage.py check --deploy --settings=config.settings.prod

# Database operations
python manage.py migrate --settings=config.settings.dev
python manage.py makemigrations --settings=config.settings.dev

# Django shell
python manage.py shell --settings=config.settings.dev

# Create superuser
python manage.py createsuperuser --settings=config.settings.dev

# Collect static files
python manage.py collectstatic --settings=config.settings.prod

# View all settings (compare envs)
python manage.py diffsettings --settings=config.settings.prod
```

---

## 🎉 Summary

**You are here:** ✅ Phase 1 Complete | 🔴 Phase 2 Ready | 🟡 Phase 3 Planned

**Current app state is solid.** Foundation is correct. No breaking changes needed to Phase 2.

**Next step:** Read PHASE_2_SECURITY_SETUP.md and implement this week.

**Timeline to production-ready:** 1-2 weeks

**Engagement level needed:** Moderate (follow the guides, test thoroughly)

---

**Questions?** Check the phase-specific guides for detailed code examples and explanations.

**Ready?** → Open PHASE_2_SECURITY_SETUP.md and start! 🚀
