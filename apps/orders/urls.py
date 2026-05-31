"""Orders URLs"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .models import OrderViewSet

app_name = 'orders'

router = DefaultRouter()
router.register(r'', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
]
