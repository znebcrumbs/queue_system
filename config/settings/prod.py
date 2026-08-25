from .base import *
from decouple import config
from urllib.parse import parse_qs, urlparse
from django.core.exceptions import ImproperlyConfigured

DEBUG = False
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost', cast=lambda v: [s.strip() for s in v.split(',') if s.strip()])
SECRET_KEY = config('SECRET_KEY')

# PostgreSQL Configuration for Production
DATABASE_URL = config('DATABASE_URL', default='', cast=str)
if DATABASE_URL:
    parsed = urlparse(DATABASE_URL)
    query = parse_qs(parsed.query)
    sslmode = query.get('sslmode', ['require'])[0]
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': parsed.path.lstrip('/'),
            'USER': parsed.username,
            'PASSWORD': parsed.password,
            'HOST': parsed.hostname,
            'PORT': parsed.port or 5432,
            'CONN_MAX_AGE': 600,
            'OPTIONS': {
                'sslmode': sslmode,
            },
        }
    }
elif config('USE_POSTGRES', default=False, cast=bool):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='queue_system'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
            'CONN_MAX_AGE': 600,
            'OPTIONS': {
                'sslmode': config('DB_SSLMODE', default='require'),
            },
        }
    }
else:
    raise ImproperlyConfigured(
        'Production settings require PostgreSQL via DATABASE_URL or USE_POSTGRES=True. '
        'SQLite is not permitted in a commercial production environment.'
    )

# ============================================
# PRODUCTION SECURITY SETTINGS (CRITICAL)
# ============================================

# SSL/HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_REDIRECT_EXEMPT = []

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)

# Cookie Security
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
SESSION_COOKIE_HTTPONLY = config('SESSION_COOKIE_HTTPONLY', default=True, cast=bool)
SESSION_COOKIE_SAMESITE = config('SESSION_COOKIE_SAMESITE', default='Lax')

CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
CSRF_COOKIE_HTTPONLY = config('CSRF_COOKIE_HTTPONLY', default=True, cast=bool)
CSRF_COOKIE_SAMESITE = config('CSRF_COOKIE_SAMESITE', default='Lax')
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='',
    cast=lambda v: [s.strip() for s in v.split(',') if s.strip()],
)
if not CSRF_TRUSTED_ORIGINS:
    raise ImproperlyConfigured('CSRF_TRUSTED_ORIGINS must be configured in production.')

# Security Headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
