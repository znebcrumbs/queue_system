from pathlib import Path
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/topics/settings/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-only-key-change-me')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,[::1]', cast=Csv())


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

     # Custom apps
    'apps.accounts',
    'apps.queues',
    'apps.survey',
    'apps.audit',
    'rest_framework',
]

KIOSK_API_KEY = config('KIOSK_API_KEY', default='kiosk-secret-key')

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
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'apps.queues': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

if not config('VERCEL', default=False, cast=bool):
    LOGGING['handlers']['file'] = {
        'level': 'INFO',
        'class': 'logging.FileHandler',
        'filename': BASE_DIR / 'queue_system.log',
        'formatter': 'verbose',
    }
    LOGGING['loggers']['apps.queues']['handlers'] = ['file', 'console']

AUTH_USER_MODEL = 'accounts.User'


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.accounts.api_security.APISecurityMiddleware',  # Custom API security
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
# Default to SQLite for development; override in dev.py or prod.py

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True



# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/queues/dashboard/"
LOGOUT_REDIRECT_URL = "/login/"

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
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=0, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=False, cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=False, cast=bool)

# Default security for all responses
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SECURE_REFERRER_POLICY = config('SECURE_REFERRER_POLICY', default='strict-origin-when-cross-origin')
SECURE_CROSS_ORIGIN_OPENER_POLICY = config('SECURE_CROSS_ORIGIN_OPENER_POLICY', default='same-origin')

# Cookie security defaults
SESSION_COOKIE_HTTPONLY = config('SESSION_COOKIE_HTTPONLY', default=True, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
SESSION_COOKIE_SAMESITE = config('SESSION_COOKIE_SAMESITE', default='Lax')

CSRF_COOKIE_HTTPONLY = config('CSRF_COOKIE_HTTPONLY', default=True, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_SAMESITE = config('CSRF_COOKIE_SAMESITE', default='Lax')
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000,https://localhost:8000,https://127.0.0.1:8000',
    cast=Csv(),
)
