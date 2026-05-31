"""Transactions app - Payment processing"""
from django.db import models
from django.utils import timezone
import uuid
import json
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


# ==================== MODELS ====================
class Transaction(models.Model):
    """Payment transaction"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
        ('CANCELLED', 'Cancelled'),
    ]

    PAYMENT_METHODS = [
        ('CREDIT_CARD', 'Credit Card'),
        ('DEBIT_CARD', 'Debit Card'),
        ('NET_BANKING', 'Net Banking'),
        ('UPI', 'UPI'),
        ('WALLET', 'Wallet'),
        ('MOCK', 'Mock Payment'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField('orders.Order', on_delete=models.PROTECT, related_name='transaction', db_index=True)
    user = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='transactions', db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='MOCK')
    transaction_id = models.CharField(max_length=100, unique=True, db_index=True)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'transactions'
        ordering = ['-created_at']
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['order', 'status']),
        ]

    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.status}"

    def process(self):
        """Mark as processing"""
        self.status = 'PROCESSING'
        self.processed_at = timezone.now()
        self.save()

    def complete(self):
        """Mark as completed"""
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.save()

        # Update order status
        self.order.update_status('CONFIRMED')

        # Publish event
        from .kafka_events import publish_payment_processed_event
        try:
            publish_payment_processed_event(self)
        except Exception as e:
            import logging
            logging.error(f"Failed to publish payment event: {str(e)}")

    def fail(self, error_message='Payment failed'):
        """Mark as failed"""
        self.status = 'FAILED'
        self.error_message = error_message
        self.retry_count += 1
        self.save()


class PaymentLog(models.Model):
    """Payment gateway log"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='logs', db_index=True)
    gateway_name = models.CharField(max_length=100)
    request_data = models.JSONField(default=dict)
    response_data = models.JSONField(default=dict)
    status_code = models.PositiveIntegerField()
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'payment_logs'
        ordering = ['-created_at']
        verbose_name = 'Payment Log'
        verbose_name_plural = 'Payment Logs'

    def __str__(self):
        return f"{self.gateway_name} - {self.transaction.transaction_id}"


# ==================== SERIALIZERS ====================
class PaymentLogSerializer(serializers.ModelSerializer):
    """Payment log serializer"""
    class Meta:
        model = PaymentLog
        fields = ['id', 'gateway_name', 'status_code', 'error_message', 'created_at']
        read_only_fields = fields


class TransactionSerializer(serializers.ModelSerializer):
    """Transaction serializer"""
    logs = PaymentLogSerializer(many=True, read_only=True)
    order_id = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = ['id', 'order_id', 'amount', 'status', 'payment_method', 'transaction_id', 'logs', 'created_at', 'processed_at', 'completed_at']
        read_only_fields = fields

    def get_order_id(self, obj):
        return str(obj.order.id)


class ProcessPaymentSerializer(serializers.Serializer):
    """Process payment"""
    payment_method = serializers.ChoiceField(choices=Transaction.PAYMENT_METHODS)


# ==================== VIEWS ====================
class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """Transaction management"""
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer

    def get_queryset(self):
        """Get user's transactions"""
        return Transaction.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Process payment"""
        transaction = self.get_object()
        serializer = ProcessPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if transaction.status != 'PENDING':
            return Response(
                {'error': 'Transaction is not in pending state'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Process payment
        from .payment_gateway import process_mock_payment

        transaction.payment_method = serializer.validated_data['payment_method']
        transaction.process()

        try:
            success, message = process_mock_payment(
                transaction.amount,
                transaction.transaction_id
            )

            if success:
                transaction.complete()
                return Response({
                    'message': 'Payment successful',
                    'transaction': TransactionSerializer(transaction).data
                })
            else:
                transaction.fail(message)
                return Response(
                    {'error': message},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            transaction.fail(str(e))
            return Response(
                {'error': f'Payment processing failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """Refund transaction"""
        transaction = self.get_object()

        if transaction.status != 'COMPLETED':
            return Response(
                {'error': 'Only completed transactions can be refunded'},
                status=status.HTTP_400_BAD_REQUEST
            )

        transaction.status = 'REFUNDED'
        transaction.save()

        return Response({
            'message': 'Refund initiated',
            'transaction': TransactionSerializer(transaction).data
        })
