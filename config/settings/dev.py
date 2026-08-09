from .base import *
from decouple import config
from urllib.parse import parse_qs, urlparse

DEBUG = True

# Database: PostgreSQL or SQLite
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
            'OPTIONS': {
                'sslmode': config('DB_SSLMODE', default='require'),
            },
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
