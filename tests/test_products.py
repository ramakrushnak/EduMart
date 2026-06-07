"""Tests for products app"""
import pytest
from rest_framework import status
from apps.products.models import Product


@pytest.mark.django_db
class TestProductList:
    """Test product listing"""

    def test_list_products(self, api_client, product):
        """Test listing products"""
        response = api_client.get('/api/v1/products/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0

    def test_filter_products_by_category(self, api_client, product, product_category):
        """Test filtering products by category"""
        response = api_client.get(f'/api/v1/products/?category={product_category.category}')
        assert response.status_code == status.HTTP_200_OK

    def test_search_products(self, api_client, product):
        """Test searching products"""
        response = api_client.get(f'/api/v1/products/?search={product.product_name}')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestProductDetail:
    """Test product details"""

    def test_get_product_detail(self, api_client, product):
        """Test getting product details"""
        response = api_client.get(f'/api/v1/products/{product.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['product_name'] == product.product_name

    def test_get_inventory(self, api_client, product):
        """Test getting product inventory movements"""
        response = api_client.get(f'/api/v1/products/{product.id}/inventory/')
        assert response.status_code == status.HTTP_200_OK

    def test_get_low_stock_products(self, api_client):
        """Test getting low stock products"""
        response = api_client.get('/api/v1/products/low_stock/')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestProductCategories:
    """Test product categories"""

    def test_list_categories(self, api_client, product_category):
        """Test listing categories"""
        response = api_client.get('/api/v1/products/categories/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0


@pytest.mark.django_db
class TestProductPages:
    """Test product page views"""

    def test_product_list_page(self, client, product):
        response = client.get('/products/')
        assert response.status_code == 200
        assert b'Explore Products' in response.content

    def test_add_to_cart_requires_login(self, client, product):
        response = client.post('/products/add-to-cart/', {
            'product_id': product.id,
            'quantity': 1,
        })
        assert response.status_code == 302

    def test_add_to_cart_when_logged_in(self, client, student_user, product):
        client.force_login(student_user)
        response = client.post('/products/add-to-cart/', {
            'product_id': product.id,
            'quantity': 1,
        })
        assert response.status_code == 302
