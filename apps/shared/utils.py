"""Shared utilities - authentication, permissions, pagination, middleware"""

from rest_framework import authentication, permissions, pagination, throttling
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication as SimpleJWTAuthentication
import logging
import uuid
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
import json

logger = logging.getLogger(__name__)


# ==================== AUTHENTICATION ====================
class CustomJWTAuthentication(SimpleJWTAuthentication):
    """Custom JWT authentication with additional validation"""

    def authenticate(self, request):
        result = super().authenticate(request)

        if result is not None:
            user, validated_token = result

            # Check if token is blacklisted
            from apps.accounts.models import TokenBlacklist
            if TokenBlacklist.objects.filter(token=str(validated_token)).exists():
                raise AuthenticationFailed('Token has been blacklisted')

            return user, validated_token

        return None


# ==================== PERMISSIONS ====================
class IsStudent(permissions.BasePermission):
    """Check if user is a student"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'STUDENT'


class IsParent(permissions.BasePermission):
    """Check if user is a parent"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'PARENT'


class IsSchoolAdmin(permissions.BasePermission):
    """Check if user is a school admin"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['SCHOOL_ADMIN', 'SUPER_ADMIN']


class IsSuperAdmin(permissions.BasePermission):
    """Check if user is a super admin"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'SUPER_ADMIN'


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Allow owners of an object to edit it; otherwise read-only"""
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


# ==================== PAGINATION ====================
class CursorPagination(pagination.CursorPagination):
    """Cursor-based pagination for scalability"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    ordering = '-created_at'

    def paginate_queryset(self, queryset, request, view=None):
        # Extract page_size from query params
        self.page_size = min(
            int(request.query_params.get(self.page_size_query_param, self.page_size)),
            self.max_page_size
        )
        return super().paginate_queryset(queryset, request, view)


class OffsetPagination(pagination.PageNumberPagination):
    """Offset-based pagination for backward compatibility"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ==================== THROTTLING (RATE LIMITING) ====================
class AnonRateThrottle(throttling.AnonRateThrottle):
    """Anonymous user rate limit: 100 requests/hour"""
    scope = 'anon'


class UserRateThrottle(throttling.UserRateThrottle):
    """Authenticated user rate limit: 1000 requests/hour"""
    scope = 'user'


class BurstRateThrottle(throttling.SimpleRateThrottle):
    """Burst rate limiting: 10 requests/minute"""
    scope = 'burst'
    THROTTLE_RATES = {'burst': '10/min'}

    def get_cache_key(self):
        if self.request.user and self.request.user.is_authenticated:
            ident = self.request.user.pk
        else:
            ident = self.get_ident(self.request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


# ==================== MIDDLEWARE ====================
class RequestCorrelationMiddleware:
    """Add correlation ID to all requests for tracing"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Generate or extract correlation ID
        correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
        request.correlation_id = correlation_id

        response = self.get_response(request)

        # Add correlation ID to response headers
        response['X-Correlation-ID'] = correlation_id

        # Log request
        self._log_request(request, response)

        return response

    def _log_request(self, request, response):
        """Log request with correlation ID"""
        log_data = {
            'correlation_id': request.correlation_id,
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'user_id': str(request.user.id) if request.user and request.user.is_authenticated else 'anonymous',
        }
        logger.info(json.dumps(log_data))


class RequestTimeMiddleware:
    """Measure request processing time"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        import time
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time

        response['X-Process-Time'] = str(duration)
        return response


# ==================== DECORATORS ====================
def audit_action(action_type):
    """Decorator to audit user actions"""
    def decorator(func):
        def wrapper(self, request, *args, **kwargs):
            result = func(self, request, *args, **kwargs)

            # Log the action
            if request.user and request.user.is_authenticated:
                from apps.audit.models import AuditLog
                AuditLog.objects.create(
                    user=request.user,
                    action=action_type,
                    resource_type=self.serializer_class.Meta.model.__name__ if hasattr(self, 'serializer_class') else 'Unknown',
                    resource_id=kwargs.get('pk'),
                    changes={},
                )

            return result

        return wrapper

    return decorator


def cache_for_user(timeout=300):
    """Cache view response per user"""
    def decorator(func):
        def wrapper(self, request, *args, **kwargs):
            from django.core.cache import cache

            cache_key = f"user_{request.user.id}_{request.path}"

            # Try to get from cache
            cached_response = cache.get(cache_key)
            if cached_response:
                return cached_response

            response = func(self, request, *args, **kwargs)

            # Cache the response
            cache.set(cache_key, response, timeout)

            return response

        return wrapper

    return decorator


# ==================== EXCEPTION HANDLER ====================
def custom_exception_handler(exc, context):
    """Custom exception handler with logging"""
    from rest_framework.views import exception_handler

    response = exception_handler(exc, context)

    if response is None:
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return response

    # Log the exception
    log_data = {
        'error_type': exc.__class__.__name__,
        'error_message': str(exc),
        'status_code': response.status_code,
        'path': context['request'].path,
    }
    logger.warning(json.dumps(log_data))

    # Add correlation ID if available
    if hasattr(context['request'], 'correlation_id'):
        response.data['correlation_id'] = context['request'].correlation_id

    return response
