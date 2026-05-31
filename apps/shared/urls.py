"""Shared app URLs - Health checks and metrics"""
from django.urls import path
from django.http import JsonResponse
from django.db import connection
from redis import Redis
import json


def health_check(request):
    """Health check endpoint"""
    try:
        from django.conf import settings
        from apps.accounts.models import User

        health_status = {
            'status': 'healthy',
            'database': 'unknown',
            'redis': 'unknown',
            'services': {}
        }

        # Check database
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_status['database'] = 'connected'
        except Exception as e:
            health_status['database'] = f'error: {str(e)}'
            health_status['status'] = 'degraded'

        # Check Redis
        try:
            redis_client = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB
            )
            redis_client.ping()
            health_status['redis'] = 'connected'
        except Exception as e:
            health_status['redis'] = f'error: {str(e)}'

        return JsonResponse(health_status)

    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)


def metrics(request):
    """Prometheus metrics endpoint"""
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        return generate_latest(CONTENT_TYPE_LATEST), 200, {'Content-Type': CONTENT_TYPE_LATEST}
    except ImportError:
        return JsonResponse({
            'error': 'Prometheus metrics not enabled'
        }, status=503)


app_name = 'health'

urlpatterns = [
    path('', health_check, name='health_check'),
]

metrics_urls_urlpatterns = [
    path('', metrics, name='metrics'),
]
