from django.contrib import admin
from .models import ProductCategory, Product


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'display_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'category']
    ordering = ['display_order', 'name']
    fields = ['category', 'name', 'description', 'icon_url', 'display_order', 'is_active']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'category', 'sku', 'price', 'stock_quantity', 'availability_status', 'is_active']
    list_filter = ['category', 'availability_status', 'is_active']
    search_fields = ['product_name', 'sku', 'barcode', 'category__name']
    list_select_related = ['category']
    ordering = ['-created_at']
    fields = [
        'category', 'product_name', 'description', 'sku', 'barcode',
        'price', 'discount_percentage', 'tax_percentage',
        'stock_quantity', 'min_stock_level', 'availability_status',
        'images', 'is_active'
    ]
