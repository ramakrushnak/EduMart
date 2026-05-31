"""Production environment settings"""
from .base import *  # noqa

DEBUG = False
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('ALLOWED_HOSTS', 'localhost').split(',')
    if host.strip()
]
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['localhost']

# Production Database with SSL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'school_commerce'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'sslmode': 'require',
        }
    }
}

# Production Email (SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Security Settings for Production
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Content Security Policy
SECURE_CONTENT_SECURITY_POLICY = {
    'DEFAULT_SRC': ("'self'",),
    'SCRIPT_SRC': ("'self'",),
    'STYLE_SRC': ("'self'",),
}

# Production Logging
LOGGING['loggers']['django']['level'] = 'WARNING'
LOGGING['loggers']['apps']['level'] = 'WARNING'

# Metrics enabled
PROMETHEUS_METRICS_ENABLED = True
