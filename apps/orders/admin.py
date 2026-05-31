"""Django admin for orders"""
from django.contrib import admin
from .models import Order, OrderItem


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at', 'school']
    search_fields = ['user__email', 'id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Order Info', {'fields': ('id', 'user', 'school', 'status')}),
        ('Amounts', {'fields': ('subtotal', 'tax_amount', 'discount_amount', 'total_amount')}),
        ('Shipping', {'fields': ('shipping_address', 'notes')}),
        ('Dates', {'fields': ('created_at', 'updated_at', 'confirmed_at', 'shipped_at', 'delivered_at')}),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj:  # Editing an existing object
            readonly.extend(['user', 'school', 'subtotal', 'tax_amount', 'discount_amount', 'total_amount'])
        return readonly


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['product', 'order', 'quantity', 'unit_price', 'get_total']
    list_filter = ['created_at', 'order']
    search_fields = ['product__product_name', 'order__id']
    readonly_fields = ['id', 'created_at', 'get_subtotal', 'get_discount', 'get_tax', 'get_total']

    def get_subtotal(self, obj):
        return f"₹{obj.get_subtotal():.2f}"
    get_subtotal.short_description = 'Subtotal'

    def get_discount(self, obj):
        return f"₹{obj.get_discount_amount():.2f}"
    get_discount.short_description = 'Discount'

    def get_tax(self, obj):
        return f"₹{obj.get_tax_amount():.2f}"
    get_tax.short_description = 'Tax'

    def get_total(self, obj):
        return f"₹{obj.get_total():.2f}"
    get_total.short_description = 'Total'
