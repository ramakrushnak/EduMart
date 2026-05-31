"""Development environment settings"""
from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ['*']

# Development databases (single instance)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'school_commerce_dev',
        'USER': 'postgres',
        'PASSWORD': 'rkece123',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Development Email Backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Local cache/session fallback
try:
    from redis import Redis

    redis_client = Redis(host='localhost', port=6379, db=0)
    redis_client.ping()
    CACHES['default']['LOCATION'] = 'redis://localhost:6379/0'
except Exception:
    CACHES['default'] = {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'

# Celery broker
CELERY_BROKER_URL = 'amqp://guest:guest@localhost:5672//'

# Kafka
KAFKA_BROKER_URL = ['localhost:9092']

# Development logging
LOGGING['loggers']['django']['level'] = 'WARNING'
LOGGING['loggers']['apps']['level'] = 'WARNING'

# Debug toolbar
if DEBUG:
    # INSTALLED_APPS += ['debug_toolbar']
    # MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']

# Disable metrics in development
PROMETHEUS_METRICS_ENABLED = False
