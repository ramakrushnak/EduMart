"""Orders app - Order management"""
from django.db import models
from django.utils import timezone
import uuid
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


# ==================== MODELS ====================
class Order(models.Model):
    """Order model"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
        ('RETURNED', 'Returned'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='orders', db_index=True)
    school = models.ForeignKey('accounts.School', on_delete=models.PROTECT, related_name='orders', db_index=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_address = models.TextField()
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'Orders'
        ordering = ['-created_at']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['school', 'created_at']),
        ]

    def __str__(self):
        return f"Order {self.id} - {self.user.email}"

    def calculate_total(self):
        """Recalculate order total"""
        items = self.order_items.all()
        self.subtotal = sum(item.get_subtotal() for item in items)
        self.tax_amount = sum(item.get_tax_amount() for item in items)
        self.discount_amount = sum(item.get_discount_amount() for item in items)
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
        self.save()

    def update_status(self, new_status):
        """Update order status"""
        if new_status == 'CONFIRMED':
            self.confirmed_at = timezone.now()
        elif new_status == 'SHIPPED':
            self.shipped_at = timezone.now()
        elif new_status == 'DELIVERED':
            self.delivered_at = timezone.now()

        self.status = new_status
        self.save()

    def can_cancel(self):
        """Check if order can be cancelled"""
        return self.status in ['PENDING', 'CONFIRMED']

    def can_return(self):
        """Check if order can be returned"""
        return self.status in ['DELIVERED']


class OrderItem(models.Model):
    """Individual order item"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items', db_index=True)
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT, db_index=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'order_items'
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'

    def __str__(self):
        return f"{self.product.product_name} x{self.quantity}"

    def get_subtotal(self):
        """Get item subtotal without discount/tax"""
        return float(self.unit_price) * self.quantity

    def get_discount_amount(self):
        """Get discount amount"""
        subtotal = self.get_subtotal()
        return (subtotal * float(self.discount_percentage)) / 100

    def get_tax_amount(self):
        """Get tax amount"""
        subtotal = self.get_subtotal()
        discount = self.get_discount_amount()
        taxable_amount = subtotal - discount
        return (taxable_amount * float(self.tax_percentage)) / 100

    def get_total(self):
        """Get total for this item"""
        return self.get_subtotal() - self.get_discount_amount() + self.get_tax_amount()


# ==================== SERIALIZERS ====================
class OrderItemSerializer(serializers.ModelSerializer):
    """Order item serializer"""
    product_id = serializers.UUIDField(write_only=True)
    product = serializers.SerializerMethodField(read_only=True)
    subtotal = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'product', 'quantity', 'unit_price', 'discount_percentage', 'tax_percentage', 'subtotal', 'total']
        read_only_fields = ['id', 'subtotal', 'total']

    def get_product(self, obj):
        from apps.products.serializers import ProductSerializer
        return ProductSerializer(obj.product).data

    def get_subtotal(self, obj):
        return obj.get_subtotal()

    def get_total(self, obj):
        return obj.get_total()


class OrderSerializer(serializers.ModelSerializer):
    """Order serializer"""
    items = OrderItemSerializer(source='order_items', many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'status', 'subtotal', 'tax_amount', 'discount_amount', 'total_amount', 'items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class CreateOrderSerializer(serializers.Serializer):
    """Create order from cart"""
    shipping_address = serializers.CharField()
    notes = serializers.CharField(required=False, allow_blank=True)


# ==================== VIEWS ====================
class OrderViewSet(viewsets.ModelViewSet):
    """Order management"""
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        """Get user's orders"""
        return Order.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def create_from_cart(self, request):
        """Create order from user's cart"""
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from apps.carts.models import Cart

        try:
            cart = request.user.cart
        except Cart.DoesNotExist:
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        if not cart.items.exists():
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        # Create order
        order = Order.objects.create(
            user=request.user,
            school=request.user.school,
            shipping_address=serializer.validated_data['shipping_address'],
            notes=serializer.validated_data.get('notes', ''),
            total_amount=0
        )

        # Copy cart items to order
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                unit_price=cart_item.product.price,
                discount_percentage=cart_item.product.discount_percentage,
                tax_percentage=cart_item.product.tax_percentage,
            )

        # Calculate totals
        order.calculate_total()

        # Clear cart
        cart.items.all().delete()

        # Publish event
        from apps.transactions.kafka_events import publish_order_created_event
        try:
            publish_order_created_event(order)
        except Exception as e:
            import logging
            logging.error(f"Failed to publish order event: {str(e)}")

        order_serializer = OrderSerializer(order)
        return Response(order_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel order"""
        order = self.get_object()

        if not order.can_cancel():
            return Response(
                {'error': 'Order cannot be cancelled in current status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.update_status('CANCELLED')
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get order status"""
        order = self.get_object()
        return Response({
            'order_id': str(order.id),
            'status': order.status,
            'updated_at': order.updated_at,
        })
