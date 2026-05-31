"""Audit URLs"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .models import AuditLogViewSet, KafkaEventLogViewSet

app_name = 'audit'

router = DefaultRouter()
router.register(r'logs', AuditLogViewSet, basename='auditlog')
router.register(r'events', KafkaEventLogViewSet, basename='eventlog')

urlpatterns = [
    path('', include(router.urls)),
]
