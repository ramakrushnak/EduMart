"""Metrics URLs"""
from django.urls import path
from django.http import HttpResponse


def metrics_endpoint(request):
    """Prometheus metrics endpoint"""
    try:
        from prometheus_client import generate_latest
        content = generate_latest()
        return HttpResponse(content, content_type='text/plain; version=0.0.4; charset=utf-8')
    except ImportError:
        return HttpResponse('Prometheus client not available', status=503)


urlpatterns = [
    path('', metrics_endpoint, name='metrics'),
]
