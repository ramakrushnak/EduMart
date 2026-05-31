"""Pytest configuration and fixtures"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.accounts.models import School
from apps.products.models import ProductCategory, Product
from decimal import Decimal

User = get_user_model()


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Setup test database"""
    pass


@pytest.fixture
def api_client():
    """API test client"""
    return APIClient()


@pytest.fixture
def school():
    """Create test school"""
    school, _ = School.objects.get_or_create(
        code='TEST001',
        defaults={
            'name': 'Test School',
            'email': 'test@school.com',
            'phone': '9876543210',
            'address': '123 Main St',
            'city': 'Delhi',
            'state': 'Delhi',
        }
    )
    return school


@pytest.fixture
def student_user(school):
    """Create test student user"""
    user, _ = User.objects.get_or_create(
        email='student@test.com',
        defaults={
            'username': 'student',
            'first_name': 'John',
            'last_name': 'Doe',
            'role': 'STUDENT',
            'school': school,
        }
    )
    user.set_password('TestPass123')
    user.save()
    return user


@pytest.fixture
def admin_user(school):
    """Create test admin user"""
    user, _ = User.objects.get_or_create(
        email='admin@test.com',
        defaults={
            'username': 'admin',
            'first_name': 'Admin',
            'last_name': 'User',
            'role': 'SCHOOL_ADMIN',
            'school': school,
            'is_staff': True,
        }
    )
    user.set_password('TestPass123')
    user.save()
    return user


@pytest.fixture
def product_category():
    """Create test product category"""
    category, _ = ProductCategory.objects.get_or_create(
        category='BAGS',
        defaults={
            'name': 'School Bags',
        }
    )
    return category


@pytest.fixture
def product(product_category):
    """Create test product"""
    product, _ = Product.objects.get_or_create(
        sku='TEST-SKU-001',
        defaults={
            'category': product_category,
            'product_name': 'Test School Bag',
            'description': 'Test product',
            'price': Decimal('299.99'),
            'discount_percentage': Decimal('5'),
            'tax_percentage': Decimal('5'),
            'stock_quantity': 100,
        }
    )
    return product


@pytest.fixture
def authenticated_client(api_client, student_user):
    """Authenticated API client"""
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(student_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    api_client.user = student_user
    return api_client
