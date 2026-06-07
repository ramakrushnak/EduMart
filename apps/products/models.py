"""Products app - models, serializers, views, and services"""
from django.db import models
import uuid
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
# from django.views.decorators.cache import cache_page
# from django.views.decorators.cache import cache_page as cache_decorator
from django_filters import CharFilter, NumberFilter, FilterSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated


# ==================== MODELS ====================
class ProductCategory(models.Model):
    """Product categories"""
    CATEGORIES = [
        ('BAGS', 'School Bags'),
        ('STATIONERY', 'Stationery'),
        ('UNIFORMS', 'Uniforms'),
        ('SANITARY', 'Sanitary Products'),
        ('SPORTS', 'Sports Equipment'),
        ('CLASSROOM', 'Classroom Supplies'),
        ('MEDALS', 'Medals & Trophies'),
        ('OFFICE', 'Office Supplies'),
        ('ACCESSORIES', 'Other Accessories'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.CharField(max_length=50, choices=CATEGORIES, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    icon_url = models.URLField(blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product_categories'
        ordering = ['display_order', 'name']
        verbose_name = 'Product Category'
        verbose_name_plural = 'Product Categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    """Product catalog"""
    AVAILABILITY_CHOICES = [
        ('IN_STOCK', 'In Stock'),
        ('LOW_STOCK', 'Low Stock'),
        ('OUT_OF_STOCK', 'Out of Stock'),
        ('DISCONTINUED', 'Discontinued'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT, related_name='products', db_index=True)
    product_name = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    sku = models.CharField(max_length=100, unique=True, db_index=True)
    barcode = models.CharField(max_length=100, blank=True, null=True, unique=True, db_index=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=5)
    stock_quantity = models.PositiveIntegerField(default=0)
    min_stock_level = models.PositiveIntegerField(default=10)
    availability_status = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='IN_STOCK', db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    images = models.JSONField(default=list)  # List of image URLs
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        ordering = ['-created_at']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['availability_status']),
        ]

    def __str__(self):
        return self.product_name

    def get_final_price(self):
        """Calculate final price with discount and tax"""
        discount_amount = (self.price * self.discount_percentage) / 100
        discounted_price = self.price - discount_amount
        tax_amount = (discounted_price * self.tax_percentage) / 100
        return discounted_price + tax_amount


class Inventory(models.Model):
    """Inventory tracking"""
    MOVEMENT_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('RETURN', 'Return'),
        ('ADJUSTMENT', 'Adjustment'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_movements', db_index=True)
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES, db_index=True)
    quantity_change = models.IntegerField()
    reason = models.CharField(max_length=255)
    reference_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'inventory_movements'
        ordering = ['-created_at']
        verbose_name = 'Inventory Movement'
        verbose_name_plural = 'Inventory Movements'
        indexes = [
            models.Index(fields=['product', 'created_at']),
            models.Index(fields=['reference_id']),
        ]

    def __str__(self):
        return f"{self.product} - {self.movement_type}"


# ==================== SERIALIZERS ====================
class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ['id', 'category', 'name', 'description', 'icon_url', 'is_active']


class ProductSerializer(serializers.ModelSerializer):
    category = ProductCategorySerializer(read_only=True)
    final_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'category', 'product_name', 'description', 'sku', 'barcode',
            'price', 'discount_percentage', 'tax_percentage', 'final_price',
            'stock_quantity', 'availability_status', 'images', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'final_price']

    def get_final_price(self, obj: Product) -> float:
        return float(obj.get_final_price())


class ProductDetailSerializer(ProductSerializer):
    """Detailed product view"""
    average_rating = serializers.SerializerMethodField()

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ['average_rating']
        read_only_fields = ProductSerializer.Meta.read_only_fields + ['average_rating']

    def get_average_rating(self, obj: Product) -> float:
        return 4.5


class InventoryMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = ['id', 'product', 'movement_type', 'quantity_change', 'reason', 'created_at']
        read_only_fields = ['id', 'created_at']


# ==================== FILTERS ====================
class ProductFilter(FilterSet):
    category = CharFilter(field_name='category__category', lookup_expr='exact')
    min_price = NumberFilter(field_name='price', lookup_expr='gte')
    max_price = NumberFilter(field_name='price', lookup_expr='lte')

    class Meta:
        model = Product
        fields = ['category', 'availability_status', 'is_active']


# ==================== SERVICES ====================
class ProductService:
    """Product business logic"""

    @staticmethod
    def update_inventory(product_id, quantity_change, movement_type, reason, reference_id=None):
        """Update product inventory and create movement record"""
        try:
            product = Product.objects.get(id=product_id)
            product.stock_quantity += quantity_change
            product.save()

            Inventory.objects.create(
                product=product,
                movement_type=movement_type,
                quantity_change=quantity_change,
                reason=reason,
                reference_id=reference_id
            )

            # Update availability status
            if product.stock_quantity <= 0:
                product.availability_status = 'OUT_OF_STOCK'
            elif product.stock_quantity <= product.min_stock_level:
                product.availability_status = 'LOW_STOCK'
            else:
                product.availability_status = 'IN_STOCK'
            product.save()

            return product
        except Product.DoesNotExist:
            raise ValueError(f"Product {product_id} not found")

    @staticmethod
    def get_low_stock_products(threshold=None):
        """Get products with low stock"""
        return Product.objects.filter(
            stock_quantity__lte=models.F('min_stock_level'),
            is_active=True
        )


# ==================== VIEWS ====================
class ProductCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Product categories - read only"""
    queryset = ProductCategory.objects.filter(is_active=True)
    serializer_class = ProductCategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    ordering_fields = ['display_order', 'name']
    ordering = ['display_order']


class ProductViewSet(viewsets.ModelViewSet):
    """Product management"""
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_class = ProductFilter
    search_fields = ['product_name', 'sku', 'barcode']
    ordering_fields = ['price', 'created_at', 'stock_quantity']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductSerializer

    @action(detail=True, methods=['get'])
    def inventory(self, request, pk=None):
        """Get inventory movements for a product"""
        product = self.get_object()
        movements = product.inventory_movements.all()[:100]
        serializer = InventoryMovementSerializer(movements, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get products with low stock"""
        products = ProductService.get_low_stock_products()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
