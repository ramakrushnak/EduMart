"""Notifications URLs"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .models import NotificationViewSet

app_name = 'notifications'

router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]
