"""Products URLs"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .models import ProductCategoryViewSet, ProductViewSet

app_name = 'products'

router = DefaultRouter()
router.register(r'categories', ProductCategoryViewSet, basename='category')
router.register(r'', ProductViewSet, basename='product')

urlpatterns = [
    path('', include(router.urls)),
]
