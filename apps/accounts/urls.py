"""Accounts app URLs"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginViewSet, RegisterViewSet, UserViewSet, SchoolViewSet,
    CustomTokenObtainPairView
)

app_name = 'accounts'

router = DefaultRouter()
router.register(r'login', LoginViewSet, basename='login')
router.register(r'register', RegisterViewSet, basename='register')
router.register(r'users', UserViewSet, basename='user')
router.register(r'schools', SchoolViewSet, basename='school')

urlpatterns = [
    path('', include(router.urls)),
    path('token/obtain/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
