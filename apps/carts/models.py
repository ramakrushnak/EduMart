"""Carts app - Shopping cart with Redis caching"""
from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache


# ==================== MODELS ====================
class Cart(models.Model):
    """Shopping cart"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='cart', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        db_table = 'carts'
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'

    def __str__(self):
        return f"Cart for {self.user.email}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=30)
        super().save(*args, **kwargs)

    def get_total(self):
        """Calculate cart total"""
        return sum(item.get_subtotal() for item in self.items.all())

    def get_item_count(self):
        """Get total items in cart"""
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    """Individual cart item"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', db_index=True)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, db_index=True)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cart_items'
        unique_together = ['cart', 'product']
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'

    def __str__(self):
        return f"{self.product.product_name} x{self.quantity}"

    def get_subtotal(self):
        """Calculate item subtotal with tax"""
        return float(self.product.get_final_price()) * self.quantity


# ==================== SERIALIZERS ====================
class CartItemSerializer(serializers.ModelSerializer):
    """Cart item serializer"""
    product_id = serializers.UUIDField(write_only=True)
    product = serializers.SerializerMethodField(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product_id', 'product', 'quantity', 'subtotal', 'added_at']
        read_only_fields = ['id', 'added_at']

    def get_product(self, obj):
        from apps.products.serializers import ProductSerializer
        return ProductSerializer(obj.product).data

    def get_subtotal(self, obj):
        return obj.get_subtotal()


class CartSerializer(serializers.ModelSerializer):
    """Cart serializer"""
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total', 'item_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_total(self, obj):
        return obj.get_total()

    def get_item_count(self, obj):
        return obj.get_item_count()


class AddToCartSerializer(serializers.Serializer):
    """Add item to cart"""
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, max_value=100)


class UpdateCartItemSerializer(serializers.Serializer):
    """Update cart item"""
    quantity = serializers.IntegerField(min_value=1, max_value=100)


# ==================== CACHE SERVICE ====================
class CartCacheService:
    """Redis cache operations for cart"""

    @staticmethod
    def get_cache_key(user_id):
        return f"cart:{user_id}"

    @staticmethod
    def get_cart(user_id):
        """Get cart from cache"""
        cache_key = CartCacheService.get_cache_key(user_id)
        cart_data = cache.get(cache_key)
        return cart_data

    @staticmethod
    def save_cart(user_id, cart_data):
        """Save cart to cache"""
        cache_key = CartCacheService.get_cache_key(user_id)
        cache.set(cache_key, cart_data, timeout=30*24*60*60)  # 30 days

    @staticmethod
    def delete_cart(user_id):
        """Delete cart from cache"""
        cache_key = CartCacheService.get_cache_key(user_id)
        cache.delete(cache_key)

    @staticmethod
    def update_cache_ttl(user_id):
        """Update cache TTL (sliding window)"""
        cache_key = CartCacheService.get_cache_key(user_id)
        cache_data = cache.get(cache_key)
        if cache_data:
            cache.set(cache_key, cache_data, timeout=30*24*60*60)


# ==================== VIEWS ====================
class CartViewSet(viewsets.ViewSet):
    """Cart management"""
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Get user's cart"""
        try:
            cart = request.user.cart
            serializer = CartSerializer(cart)
            return Response(serializer.data)
        except Cart.DoesNotExist:
            # Create new cart
            cart = Cart.objects.create(user=request.user)
            serializer = CartSerializer(cart)
            return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """Add item to cart"""
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart, _ = Cart.objects.get_or_create(user=request.user)

        # Get product
        from apps.products.models import Product
        try:
            product = Product.objects.get(id=serializer.validated_data['product_id'], is_active=True)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        # Add or update item
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': serializer.validated_data['quantity']}
        )

        if not created:
            item.quantity += serializer.validated_data['quantity']
            item.save()

        # Clear cache
        CartCacheService.delete_cart(str(request.user.id))

        cart_serializer = CartSerializer(cart)
        return Response(cart_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['put'])
    def update_item(self, request):
        """Update cart item quantity"""
        item_id = request.data.get('item_id')
        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            item = CartItem.objects.get(id=item_id, cart__user=request.user)
            item.quantity = serializer.validated_data['quantity']
            item.save()

            # Clear cache
            CartCacheService.delete_cart(str(request.user.id))

            cart_serializer = CartSerializer(item.cart)
            return Response(cart_serializer.data)
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['delete'])
    def remove_item(self, request):
        """Remove item from cart"""
        item_id = request.query_params.get('item_id')

        try:
            item = CartItem.objects.get(id=item_id, cart__user=request.user)
            cart = item.cart
            item.delete()

            # Clear cache
            CartCacheService.delete_cart(str(request.user.id))

            cart_serializer = CartSerializer(cart)
            return Response(cart_serializer.data)
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def clear(self, request):
        """Clear entire cart"""
        try:
            cart = request.user.cart
            cart.items.all().delete()

            # Clear cache
            CartCacheService.delete_cart(str(request.user.id))

            return Response({'message': 'Cart cleared'})
        except Cart.DoesNotExist:
            return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def toggle_wishlist(self, request):
        """Toggle wishlist for product"""
        product_id = request.data.get('product_id')

        from apps.products.models import Product
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        cart, _ = Cart.objects.get_or_create(user=request.user)

        # Check if already in wishlist
        wishlist_item = CartItem.objects.filter(
            cart=cart,
            product=product
        ).first()

        if wishlist_item:
            wishlist_item.delete()
            return Response({'message': 'Removed from wishlist'})
        else:
            CartItem.objects.create(cart=cart, product=product, quantity=0)
            return Response({'message': 'Added to wishlist'})
