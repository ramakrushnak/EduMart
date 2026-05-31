"""URL Configuration for EduMart"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    # Admin
    path('admin/', admin.site.urls),

    # Health Check
    path('health/', include('apps.shared.urls', namespace='health')),

    # API v1
    path('api/v1/auth/', include('apps.accounts.urls', namespace='accounts')),
    path('api/v1/products/', include('apps.products.urls', namespace='products')),
    path('api/v1/cart/', include('apps.carts.urls', namespace='carts')),
    path('api/v1/orders/', include('apps.orders.urls', namespace='orders')),
    path('api/v1/transactions/', include('apps.transactions.urls', namespace='transactions')),
    path('api/v1/notifications/', include('apps.notifications.urls', namespace='notifications')),
    path('api/v1/audit/', include('apps.audit.urls', namespace='audit')),

    # OpenAPI / Swagger Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Metrics
    path('metrics/', include('apps.shared.metrics_urls')),
]

# Media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Debug toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
