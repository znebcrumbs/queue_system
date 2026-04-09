# ✅ PHASE 2 IMPLEMENTATION CHECKLIST

**Estimated Time:** 45 minutes  
**Difficulty:** Moderate (copy-paste code snippets)  
**Risk Level:** Low (all changes are additive, no breaking changes)

---

## 📋 PRE-IMPLEMENTATION (5 minutes)

- [ ] **Read** `PHASE_2_SECURITY_SETUP.md` - Understand what each change does
- [ ] **Backup** current settings files (optional but recommended):
  ```powershell
  Copy-Item config/settings/base.py config/settings/base.py.backup
  Copy-Item config/settings/dev.py config/settings/dev.py.backup
  Copy-Item config/settings/prod.py config/settings/prod.py.backup
  ```
- [ ] **Test** current app works:
  ```powershell
  python manage.py runserver
  # Should see: Starting development server at http://127.0.0.1:8000/
  ```
- [ ] Open VS Code and have all 3 settings files ready to edit

---

## 🔧 STEP 1: UPDATE `config/settings/base.py` (10 minutes)

### Action: ADD security headers at END of file

- [ ] Open `config/settings/base.py`
- [ ] Scroll to the BOTTOM (after LOGGING section)
- [ ] **Copy** this entire block from `PHASE_2_SECURITY_SETUP.md` (Section 1)
- [ ] **Paste** at the end of base.py
- [ ] **Save** the file

### What was added:
- ✅ X_FRAME_OPTIONS (prevent clickjacking)
- ✅ SECURE_CONTENT_TYPE_NOSNIFF (prevent MIME sniffing)
- ✅ SECURE_BROWSER_XSS_FILTER (XSS protection)
- ✅ REFERRER_POLICY (referrer control)
- ✅ PERMISSIONS_POLICY (browser API restrictions)
- ✅ SECURE_HSTS_* (HSTS config)
- ✅ CSRF_COOKIE_HTTPONLY

### ✅ Verification:
```powershell
python manage.py runserver
# Should work normally, no errors expected
```

---

## 🔧 STEP 2: UPDATE `config/settings/dev.py` (10 minutes)

### Action: REPLACE entire file with new dev-specific config

- [ ] Open `config/settings/dev.py`
- [ ] **Select All** (Ctrl+A)
- [ ] **Delete** the entire content
- [ ] **Copy** the new dev.py content from `PHASE_2_SECURITY_SETUP.md` (Section 3)
- [ ] **Paste** the new content
- [ ] **Save** the file

### What changed:
- ✅ Database config (can use SQLite or PostgreSQL)
- ✅ SESSION_COOKIE_SECURE = False (OK for local http://)
- ✅ CSRF_TRUSTED_ORIGINS configured for localhost
- ✅ SECURE_SSL_REDIRECT = False (no HTTPS required in dev)
- ✅ Proper logging config for development
- ✅ Debug toolbar support

### ✅ Verification:
```powershell
# Test with default settings (dev)
python manage.py runserver
# Should work: http://127.0.0.1:8000/

# Test creating a superuser
python manage.py createsuperuser
# Should work for creating test user

# Test database
python manage.py migrate
# Should run migrations successfully
```

---

## 🔧 STEP 3: UPDATE `config/settings/prod.py` (10 minutes)

### Action: REPLACE entire file with new prod-specific config

- [ ] Open `config/settings/prod.py`
- [ ] **Select All** (Ctrl+A)
- [ ] **Delete** the entire content
- [ ] **Copy** the new prod.py content from `PHASE_2_SECURITY_SETUP.md` (Section 2)
- [ ] **Paste** the new content
- [ ] **Save** the file

### What changed:
- ✅ DEBUG = False (hardcoded, safety mechanism)
- ✅ ALLOWED_HOSTS from environment variable
- ✅ PostgreSQL REQUIRED (not optional)
- ✅ SECURE_SSL_REDIRECT = True (force HTTPS)
- ✅ SESSION_COOKIE_SECURE = True (HTTPS only)
- ✅ SESSION_COOKIE_HTTPONLY = True (no JavaScript access)
- ✅ SESSION_COOKIE_SAMESITE = 'Strict' (CSRF protection)
- ✅ CSRF_COOKIE_SECURE = True (HTTPS only)
- ✅ Security headers via inheritance from base.py
- ✅ WARNING-level logging (reduced verbosity)
- ✅ Logs directory config

### ✅ Verification - Run Django security check:
```powershell
python manage.py check --deploy --settings=config.settings.prod

# Expected output (if all good):
# System check identified no issues (0 silenced).

# If errors: fix them before continuing
```

---

## 🔧 STEP 4: VERIFY `.env` FILE (5 minutes)

### Action: Ensure .env has all required variables

- [ ] Open `.env` file
- [ ] Verify these variables exist:
  ```
  ✅ DEBUG=True                     (dev default, OK)
  ✅ SECRET_KEY=...                (some value set)
  ✅ ALLOWED_HOSTS=...             (localhost,127.0.0.1 OK for dev)
  ✅ KIOSK_API_KEY=...             (set in the file ✅)
  ✅ USE_POSTGRES=True             (if using PostgreSQL)
  ✅ DB_NAME, DB_USER, DB_PASSWORD (if USE_POSTGRES=True)
  ```

- [ ] For production, you would:
  - Create `.env.production`
  - Use the template from `.env.example`
  - Change all values to production secrets

### Current .env status:
- ✅ All required variables present
- ✅ KIOSK_API_KEY added ✅
- ✅ No need to change for local development

---

## 🧪 STEP 5: TEST LOCALLY WITH DEV SETTINGS (10 minutes)

### Test 1: Dev mode (current default)
```powershell
python manage.py runserver

# Expected: Server runs on http://127.0.0.1:8000/
# No errors about missing config
```

### Test 2: Prod mode with DEBUG=False
```powershell
# Temporarily set DEBUG=False
$env:DEBUG="False"

python manage.py runserver --settings=config.settings.prod --nothreading

# Expected: 
# - Server starts (might show static file warning, that's OK)
# - Admin/login pages work
# - JSON endpoints work

# Ctrl+C to stop
```

### Test 3: Security check
```powershell
python manage.py check --deploy --settings=config.settings.prod

# Expected output:
# System check identified no issues (0 silenced).

# If you see errors, note them - they're security warnings
```

### Test 4: Verify endpoints work
```powershell
python manage.py runserver

# Open in browser:
# ✅ http://127.0.0.1:8000/admin/          (login required)
# ✅ http://127.0.0.1:8000/login/          (should work)
# ✅ http://127.0.0.1:8000/queues/         (login required)
```

---

## 🔐 STEP 6: VERIFY ENDPOINT PROTECTION (5 minutes)

### Check 1: Kiosk endpoints protected
```powershell
# These should NOT work without API key:
curl -X POST http://127.0.0.1:8000/queues/create_queue_entry/

# Expected: 403 Unauthorized (good!)
# If you get different error, check logs
```

### Check 2: Authenticated endpoints protected
```powershell
# Try to access without login:
curl http://127.0.0.1:8000/queues/

# Expected: Redirect to login (good!)
```

### Check 3: Admin protected
```powershell
# Try to access admin without login:
curl http://127.0.0.1:8000/admin/

# Expected: Redirect to login (good!)
```

---

## ✅ STEP 7: FINAL VERIFICATION CHECKLIST (5 minutes)

- [ ] **Config files updated:**
  - [ ] base.py has security headers section
  - [ ] dev.py is updated with database config
  - [ ] prod.py is production-secure

- [ ] **Environment variables:**
  - [ ] .env file has SECRET_KEY
  - [ ] .env file has KIOSK_API_KEY
  - [ ] .env.example is a good template

- [ ] **Django checks passed:**
  - [ ] `python manage.py runserver` works (dev)
  - [ ] `python manage.py check --deploy` passes (prod)
  - [ ] No Python import errors
  - [ ] Database migrations work

- [ ] **Security verified:**
  - [ ] Kiosk endpoints require API key
  - [ ] Authenticated endpoints require login
  - [ ] DEBUG=False doesn't break app
  - [ ] Static files work (or acceptable warning)

- [ ] **No regressions:**
  - [ ] Admin still accessible
  - [ ] Login page loads
  - [ ] Queue views work
  - [ ] API endpoints respond

---

## 🎯 PHASE 2 COMPLETE WHEN:

✅ **All 7 steps above are done**
✅ **All checkboxes are checked**
✅ **Security check passes**
✅ **No errors in logs**

---

## 📞 TROUBLESHOOTING

### Problem: "0.0.0.0 host not allowed"
**Fix:** Check ALLOWED_HOSTS in dev.py
```python
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '0.0.0.0']  # Add '0.0.0.0'
```

### Problem: "static files not found" with DEBUG=False
**This is expected!** Run:
```powershell
python manage.py collectstatic --settings=config.settings.prod --no-input
```

### Problem: "Can't find config.settings module"
**Fix:** Check DJANGO_SETTINGS_MODULE environment variable
```powershell
echo $env:DJANGO_SETTINGS_MODULE
# Should be: config.settings.dev (or not set, uses default)
```

### Problem: "KIOSK_API_KEY not found"
**Fix:** Ensure .env has:
```
KIOSK_API_KEY=dev-kiosk-api-key-change-in-production
```

### Problem: Database password wrong
**Fix:** Update .env with correct credentials:
```
DB_USER=postgres
DB_PASSWORD=your-actual-password
DB_HOST=localhost
```

---

## 📚 REFERENCE - FILE LOCATIONS

All files are in the project root:
- `config/settings/base.py` - Shared settings (add security headers)
- `config/settings/dev.py` - Dev-only settings (replace entirely)
- `config/settings/prod.py` - Prod-only settings (replace entirely)
- `.env` - Local secrets (already updated ✅)
- `.env.example` - Template (updated ✅)
- `PHASE_2_SECURITY_SETUP.md` - Full guide with code

---

## ⏭️ WHAT'S NEXT

After completing PHASE 2:

1. **Commit changes to git:**
   ```powershell
   git add config/settings/
   git add .env.example
   git commit -m "PHASE 2: Critical security hardening"
   ```

2. **Test on staging environment** (if you have one)

3. **Prepare for PHASE 3:**
   - Read `PHASE_3_SYSTEM_DESIGN.md`
   - Plan Organization model
   - Estimate effort for Ticket model

4. **Optional: Production deployment**
   - Create `.env.production` file
   - Copy to production server (securely!)
   - Run migrations on production DB
   - Test thoroughly before going live

---

## ✨ YOU ARE HERE

```
PHASE 1 (Foundation)
   ✅ COMPLETE
   
PHASE 2 (Security)
   🔴 NOW DOING THIS
   ← You are here following this checklist
   
PHASE 3 (Architecture)
   🟡 NEXT (after Phase 2)
```

**Estimated time to complete:** 45 minutes

**Next step:** Start with STEP 1 above! 🚀

---

**Print this checklist and check off each box as you complete them!**

Good luck! 💪
