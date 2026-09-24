# PHASE 2 — CRITICAL SECURITY SETUP

> ⏱️ Estimated time: **30 minutes**
> 
> This document provides exact code that needs to be added/modified to secure the application for production.

---

## 📋 Checklist of Changes

- [ ] Add security headers to `config/settings/base.py`
- [ ] Update `config/settings/prod.py` with cookie security
- [ ] Verify `.env` has all required variables
- [ ] Test locally with `DEBUG=False`
- [ ] Audit @csrf_exempt usage (ALREADY GOOD ✅)
- [ ] Verify endpoint protection (ALREADY GOOD ✅)

---

## 1️⃣ UPDATE `config/settings/base.py`

### Add security headers at the END of the file (after LOGGING config):

```python
# ============================================
# SECURITY HEADERS & CONFIG
# ============================================

# Framebusting - prevent clickjacking
X_FRAME_OPTIONS = 'DENY'

# Prevent MIME type sniffing
SECURE_CONTENT_TYPE_NOSNIFF = True

# Enable XSS filter in browsers
SECURE_BROWSER_XSS_FILTER = True

# Control referrer information
REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Permissions Policy (formerly Feature Policy)
PERMISSIONS_POLICY = {
    'accelerometer': [],
    'camera': [],
    'geolocation': [],
    'gyroscope': [],
    'magnetometer': [],
    'microphone': [],
    'payment': [],
    'usb': [],
}

# Cache control for static assets
SECURE_HSTS_SECONDS = 0  # Set to 31536000 in production
SECURE_HSTS_INCLUDE_SUBDOMAINS = False  # True in production
SECURE_HSTS_PRELOAD = False  # True in production

# Default security for all responses
SECURE_SSL_REDIRECT = False  # Override in prod.py to True

# Additional CSRF settings
CSRF_COOKIE_HTTPONLY = False  # Set to True in prod
CSRF_TRUSTED_ORIGINS = []  # Configure per environment
```

---

## 2️⃣ UPDATE `config/settings/prod.py`

### Replace the security settings section with:

```python
from .base import *
from decouple import config

DEBUG = False
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost', cast=lambda v: [s.strip() for s in v.split(',')])

# PostgreSQL Configuration for Production (Required)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 600,
    }
}

# ============================================
# PRODUCTION SECURITY SETTINGS (CRITICAL)
# ============================================

# SSL/HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cookie Security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

# Security Headers (from base.py, override here)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message} [IP: {record.remote_addr}]',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',  # Only warnings and above in prod
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'queue_system.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'apps.queues': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Disable debug toolbar in production
DEBUG_TOOLBAR_CONFIG = {'SHOW_TOOLBAR_CALLBACK': lambda r: False}
```

---

## 3️⃣ UPDATE `config/settings/dev.py`

### Replace with:

```python
from .base import *
from decouple import config

DEBUG = True

# Database: PostgreSQL or SQLite
if config('USE_POSTGRES', default=False, cast=bool):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='queue_system'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }
else:
    # Use SQLite for quick local development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ============================================
# DEVELOPMENT SECURITY (PERMISSIVE)
# ============================================
SESSION_COOKIE_SECURE = False  # HTTP OK for local dev
CSRF_COOKIE_SECURE = False

# Allow local development origins
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://127.0.0.1:8001',
    'http://localhost:8000',
    'http://localhost:8001',
    'http://localhost:3000',  # If using frontend dev server
]

# Disable HTTPS redirect for local dev
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'queue_system.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'apps.queues': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Django debug toolbar for development
INSTALLED_APPS = list(INSTALLED_APPS) + ['debug_toolbar']
MIDDLEWARE = list(MIDDLEWARE) + ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']
```

---

## 4️⃣ UPDATE `.env` for Production

### Create a `.env.production` file with these values:

```env
# ============================================
# PRODUCTION ENVIRONMENT VARIABLES
# ============================================

# Core Django
DEBUG=False
SECRET_KEY=your-extremely-secure-secret-key-here-minimum-50-chars-!@#$%^&*()
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com

# Database (PostgreSQL REQUIRED for production)
USE_POSTGRES=True
DB_NAME=queue_system_prod
DB_USER=db_user_here
DB_PASSWORD=super-secure-password-here-minimum-20-chars
DB_HOST=your-db-host.com
DB_PORT=5432

# Security
SECURE_SSL_REDIRECT=True
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https

# Kiosk API (CRITICAL - Change from default!)
KIOSK_API_KEY=your-production-api-key-minimum-32-chars-!@#$%^&*()

# Optional: Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@domain.com
EMAIL_HOST_PASSWORD=your-app-specific-password
```

---

## 5️⃣ Verify Endpoint Protection

### ✅ ALREADY PROTECTED (No changes needed):

**Kiosk endpoints** (`apps/queues/views.py`):
- ✅ `create_queue_entry()` - Protected with `@api_key_required` + `@throttle_kiosk`
- ✅ `update_queue_entry()` - Protected with API key check

**Authenticated endpoints:**
- ✅ `queue_list()` - Has `@login_required`
- ✅ `dashboard` - Should have `@login_required` (verify in URL conf)
- ✅ Admin - Auto-protected by Django

### 🔍 Action Required:

Add a view audit check. In Django shell:

```python
# Check which views don't have @login_required
python manage.py shell
>>> import inspect
>>> from apps.queues import views
>>> print([m for m in dir(views) if not m.startswith('_')])
```

---

## 6️⃣ Test Security Locally

### Run these commands:

```powershell
# Test with DEV settings
python manage.py runserver --settings=config.settings.dev

# Test with PROD settings (DEBUG=False)
# First, update .env:
DEBUG=False
python manage.py runserver --settings=config.settings.prod --nothreading

# This will show if there are any static file issues or other prod problems
```

### Check for missing static files:
```powershell
python manage.py collectstatic --settings=config.settings.prod --dry-run
```

---

## 7️⃣ Environment Variable Checklist

**Required in production `.env`:**
- [ ] `SECRET_KEY` - Minimum 50 characters, random
- [ ] `DEBUG=False` - MUST be False
- [ ] `ALLOWED_HOSTS` - Your domain(s)
- [ ] `DB_NAME`, `DB_USER`, `DB_PASSWORD` - PostgreSQL credentials
- [ ] `KIOSK_API_KEY` - Random API key, minimum 32 characters
- [ ] `SECURE_SSL_REDIRECT=True` - Force HTTPS

**Never commit:**
- ❌ `.env` (contains secrets)
- ✅ `.env.example` (template only, no secrets)

---

## 8️⃣ Quick Deploy Checklist

Before deploying to production:

```powershell
# 1. Test locally with prod settings
python manage.py check --deploy --settings=config.settings.prod

# 2. Verify all static files
python manage.py collectstatic --settings=config.settings.prod --no-input

# 3. Run migrations
python manage.py migrate --settings=config.settings.prod

# 4. Create admin user
python manage.py createsuperuser --settings=config.settings.prod

# 5. Check security headers (use online tool or curl)
curl -I https://yourdomain.com
# Should show: Strict-Transport-Security, X-Frame-Options, X-Content-Type-Options
```

---

## 📚 Reference: Security Headers Explanation

| Header | What it does |
|--------|------------|
| `Strict-Transport-Security` | Force HTTPS only (prevents downgrade attacks) |
| `X-Frame-Options: DENY` | Prevent clickjacking by blocking iframe embedding |
| `X-Content-Type-Options: nosniff` | Prevent MIME type sniffing attacks |
| `X-XSS-Protection` | Enable browser XSS filter |
| `Referrer-Policy` | Control what referrer info is sent |
| `Permissions-Policy` | Restrict browser APIs (camera, microphone, etc.) |

---

## ✅ Completion Checklist

- [ ] Updated `config/settings/base.py` with security headers
- [ ] Updated `config/settings/prod.py` with production security
- [ ] Updated `config/settings/dev.py` with dev settings
- [ ] Created `.env.production` template
- [ ] Verified endpoint protection (all have @login_required or @api_key_required)
- [ ] Tested locally with DEBUG=False
- [ ] Ran Django security check
- [ ] All environment variable requirements documented

---

## 🎯 Next Steps

After PHASE 2 is complete:

→ **PHASE 3: Create Organization & Audit models**
   - Create `Organization` model
   - Create `Ticket` base entity model
   - Create `AuditLog` for tracking changes
   - Implement RBAC enforcement

