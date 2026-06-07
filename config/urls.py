"""URL Configuration for EduMart"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from apps.products import views as product_views
from apps.carts import views as cart_views
from apps.orders import views as orders_views
from apps.accounts.auth_views import login_page, register_page, logout_page

urlpatterns = [
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    # Admin
    path('admin/', admin.site.urls),
    # Authentication
    path('login/', login_page, name='login_page'),
    path('register/', register_page, name='register_page'),
    path('logout/', logout_page, name='logout_page'),
    # Product browsing
    path('products/', product_views.product_list, name='product_list'),
    path('products/add-to-cart/', product_views.add_to_cart, name='add_to_cart'),
    path('orders/', orders_views.orders_list, name='orders_list'),
    path('cart/', cart_views.cart_page, name='cart_page'),
    path('cart/update-item/', cart_views.update_cart_item, name='update_cart_item'),
    path('cart/remove-item/', cart_views.remove_cart_item, name='remove_cart_item'),
    path('checkout/', cart_views.checkout, name='checkout'),
    path('order/<uuid:order_id>/confirmation/', cart_views.order_confirmation, name='order_confirmation'),
    path('cart/clear/', cart_views.clear_cart, name='clear_cart'),
    path('stationery/', product_views.product_list, name='stationery_products'),
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
