"""Django admin for transactions"""
from django.contrib import admin
from .models import Transaction, PaymentLog


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'user', 'amount', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['transaction_id', 'user__email', 'order__id']
    readonly_fields = ['id', 'transaction_id', 'created_at', 'processed_at', 'completed_at']
    fieldsets = (
        ('Transaction Info', {'fields': ('id', 'transaction_id', 'order', 'user', 'amount', 'status')}),
        ('Payment', {'fields': ('payment_method', 'reference_number')}),
        ('Retry Info', {'fields': ('retry_count', 'error_message')}),
        ('Dates', {'fields': ('created_at', 'processed_at', 'completed_at')}),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj:
            readonly.extend(['order', 'user', 'amount', 'transaction_id'])
        return readonly


@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'gateway_name', 'status_code', 'created_at']
    list_filter = ['gateway_name', 'status_code', 'created_at']
    search_fields = ['transaction__transaction_id']
    readonly_fields = ['id', 'created_at']
