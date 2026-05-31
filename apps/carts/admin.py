"""Django admin for carts"""
from django.contrib import admin
from .models import Cart, CartItem


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_item_count', 'get_total', 'created_at', 'expires_at']
    search_fields = ['user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    filter_horizontal = []

    def get_item_count(self, obj):
        return obj.get_item_count()
    get_item_count.short_description = 'Items'

    def get_total(self, obj):
        return f"₹{obj.get_total():.2f}"
    get_total.short_description = 'Total'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['product', 'cart', 'quantity', 'get_subtotal', 'added_at']
    list_filter = ['added_at', 'cart__user']
    search_fields = ['product__product_name', 'cart__user__email']
    readonly_fields = ['id', 'added_at']

    def get_subtotal(self, obj):
        return f"₹{obj.get_subtotal():.2f}"
    get_subtotal.short_description = 'Subtotal'
