"""Carts URLs"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .models import CartViewSet

app_name = 'carts'

router = DefaultRouter()
router.register(r'', CartViewSet, basename='cart')

urlpatterns = [
    path('', include(router.urls)),
]
