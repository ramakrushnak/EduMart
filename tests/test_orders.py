"""Tests for orders app"""
import pytest
from rest_framework import status
from apps.orders.models import Order
from apps.carts.models import Cart, CartItem


@pytest.mark.django_db
class TestOrderCreation:
    """Test order creation"""

    def test_create_order_from_cart(self, authenticated_client, student_user, product):
        """Test creating order from cart"""
        # Add item to cart
        cart, _ = Cart.objects.get_or_create(user=student_user)
        CartItem.objects.create(cart=cart, product=product, quantity=2)

        # Create order
        response = authenticated_client.post('/api/v1/orders/create_from_cart/', {
            'shipping_address': '123 Test St, Delhi',
            'notes': 'Please deliver carefully',
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data
        assert response.data['status'] == 'PENDING'

    def test_create_order_empty_cart(self, authenticated_client):
        """Test creating order with empty cart"""
        response = authenticated_client.post('/api/v1/orders/create_from_cart/', {
            'shipping_address': '123 Test St',
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestOrderManagement:
    """Test order management"""

    def test_list_orders(self, authenticated_client, student_user):
        """Test listing user orders"""
        # Create an order
        Order.objects.create(
            user=student_user,
            total_amount=500,
            shipping_address='Test Address'
        )

        response = authenticated_client.get('/api/v1/orders/')
        assert response.status_code == status.HTTP_200_OK

    def test_get_order_detail(self, authenticated_client, student_user):
        """Test getting order details"""
        order = Order.objects.create(
            user=student_user,
            total_amount=500,
            shipping_address='Test Address'
        )

        response = authenticated_client.get(f'/api/v1/orders/{order.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert str(response.data['id']) == str(order.id)

    def test_cancel_order(self, authenticated_client, student_user):
        """Test cancelling order"""
        order = Order.objects.create(
            user=student_user,
            status='PENDING',
            total_amount=500,
            shipping_address='Test Address'
        )

        response = authenticated_client.post(f'/api/v1/orders/{order.id}/cancel/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'CANCELLED'
