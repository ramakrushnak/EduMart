"""
Celery Tasks for Async Processing
Handles email notifications, scheduled jobs, and background processing
"""

import logging
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


# ==================== EMAIL TASKS ====================
@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_order_confirmation_email(self, order_id):
    """Send order confirmation email"""
    try:
        from apps.orders.models import Order

        order = Order.objects.get(id=order_id)
        user = order.user

        context = {
            'user_name': user.get_full_name(),
            'order_id': str(order.id),
            'total_amount': order.total_amount,
            'items': order.order_items.all(),
            'order_date': order.created_at,
        }

        subject = f'Order Confirmation - #{order.id}'
        html_message = render_to_string('emails/order_confirmation.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Order confirmation email sent for order {order_id}")
        return f"Email sent for order {order_id}"

    except Exception as exc:
        logger.error(f"Failed to send order confirmation email: {str(exc)}")
        raise self.retry(exc=exc, countdown=300)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_payment_receipt_email(self, transaction_id):
    """Send payment receipt email"""
    try:
        from apps.transactions.models import Transaction

        transaction = Transaction.objects.select_related('order', 'order__user').get(id=transaction_id)
        user = transaction.order.user

        context = {
            'user_name': user.get_full_name(),
            'transaction_id': str(transaction.id),
            'order_id': str(transaction.order_id),
            'amount': transaction.amount,
            'status': transaction.status,
            'payment_method': transaction.payment_method,
            'transaction_date': transaction.created_at,
        }

        subject = f'Payment Receipt - Order #{transaction.order_id}'
        html_message = render_to_string('emails/payment_receipt.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Payment receipt email sent for transaction {transaction_id}")
        return f"Receipt email sent for transaction {transaction_id}"

    except Exception as exc:
        logger.error(f"Failed to send payment receipt email: {str(exc)}")
        raise self.retry(exc=exc, countdown=300)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_order_status_update_email(self, order_id, new_status):
    """Send order status update email"""
    try:
        from apps.orders.models import Order

        order = Order.objects.get(id=order_id)
        user = order.user

        status_messages = {
            'PENDING': 'Your order is being processed',
            'CONFIRMED': 'Your order has been confirmed',
            'SHIPPED': 'Your order has been shipped',
            'DELIVERED': 'Your order has been delivered',
            'CANCELLED': 'Your order has been cancelled',
        }

        context = {
            'user_name': user.get_full_name(),
            'order_id': str(order.id),
            'status': new_status,
            'status_message': status_messages.get(new_status, ''),
        }

        subject = f'Order Status Update - #{order.id}'
        html_message = render_to_string('emails/order_status_update.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Status update email sent for order {order_id}")
        return f"Status email sent for order {order_id}"

    except Exception as exc:
        logger.error(f"Failed to send status update email: {str(exc)}")
        raise self.retry(exc=exc, countdown=300)


# ==================== MAINTENANCE TASKS ====================
@shared_task
def cleanup_expired_carts():
    """Clean up carts that haven't been accessed in 30 days"""
    try:
        from apps.carts.models import Cart

        thirty_days_ago = timezone.now() - timedelta(days=30)
        expired_carts = Cart.objects.filter(updated_at__lt=thirty_days_ago)
        count = expired_carts.count()

        expired_carts.delete()
        logger.info(f"Cleaned up {count} expired carts")
        return f"Cleaned {count} carts"

    except Exception as exc:
        logger.error(f"Failed to cleanup carts: {str(exc)}")


@shared_task
def cleanup_completed_transactions():
    """Archive/clean up old completed transactions"""
    try:
        from apps.transactions.models import Transaction

        one_year_ago = timezone.now() - timedelta(days=365)
        old_transactions = Transaction.objects.filter(
            status='COMPLETED',
            created_at__lt=one_year_ago
        )
        count = old_transactions.count()

        # In production, archive to separate database instead of deleting
        old_transactions.delete()
        logger.info(f"Cleaned up {count} old transactions")
        return f"Cleaned {count} transactions"

    except Exception as exc:
        logger.error(f"Failed to cleanup transactions: {str(exc)}")


@shared_task
def retry_failed_transactions():
    """Retry failed transactions"""
    try:
        from apps.transactions.models import Transaction
        from apps.transactions.services import process_payment

        failed_transactions = Transaction.objects.filter(
            status='FAILED',
            retry_count__lt=3
        )

        retry_count = 0
        for transaction in failed_transactions[:50]:  # Process 50 at a time
            try:
                process_payment(transaction.order)
                retry_count += 1
            except Exception as e:
                logger.error(f"Retry failed for transaction {transaction.id}: {str(e)}")
                transaction.retry_count += 1
                transaction.save()

        logger.info(f"Retried {retry_count} failed transactions")
        return f"Retried {retry_count} transactions"

    except Exception as exc:
        logger.error(f"Failed to retry transactions: {str(exc)}")


@shared_task
def generate_low_stock_alerts():
    """Generate alerts for products with low stock"""
    try:
        from apps.products.models import Product

        low_stock_products = Product.objects.filter(
            stock_quantity__lte=models.F('min_stock_level'),
            is_active=True
        )

        alert_count = 0
        for product in low_stock_products[:100]:
            # Send notification to admins
            send_low_stock_notification.delay(str(product.id), product.product_name)
            alert_count += 1

        logger.info(f"Generated {alert_count} low stock alerts")
        return f"Generated {alert_count} alerts"

    except Exception as exc:
        logger.error(f"Failed to generate low stock alerts: {str(exc)}")


@shared_task
def send_low_stock_notification(product_id, product_name):
    """Send low stock notification to admins"""
    try:
        from apps.accounts.models import User

        admins = User.objects.filter(role__in=['SCHOOL_ADMIN', 'SUPER_ADMIN'], is_active=True)

        for admin in admins:
            subject = f'Low Stock Alert: {product_name}'
            message = f'Product {product_name} has low stock and needs replenishment.'

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[admin.email],
            )

        logger.info(f"Low stock notification sent for product {product_id}")

    except Exception as exc:
        logger.error(f"Failed to send low stock notification: {str(exc)}")


# ==================== KAFKA EVENT PROCESSING TASKS ====================
@shared_task
def process_order_created_event(event_data):
    """Process order-created Kafka event"""
    try:
        from apps.orders.models import Order
        from apps.transactions.kafka_events import publish_payment_processed_event

        order_id = event_data['data']['id']
        order = Order.objects.get(id=order_id)

        # Process order payment
        from apps.transactions.services import process_payment
        transaction = process_payment(order)

        logger.info(f"Order event processed for {order_id}")
        return f"Order processed: {order_id}"

    except Exception as exc:
        logger.error(f"Failed to process order event: {str(exc)}")


@shared_task
def process_payment_event(event_data):
    """Process payment-processed Kafka event"""
    try:
        from apps.transactions.models import Transaction

        transaction_id = event_data['data']['transaction_id']
        transaction = Transaction.objects.get(id=transaction_id)

        if event_data['data']['status'] == 'COMPLETED':
            # Send confirmation email
            send_order_confirmation_email.delay(str(transaction.order_id))

        logger.info(f"Payment event processed for {transaction_id}")
        return f"Payment processed: {transaction_id}"

    except Exception as exc:
        logger.error(f"Failed to process payment event: {str(exc)}")


@shared_task
def process_inventory_event(event_data):
    """Process inventory-updated Kafka event"""
    try:
        logger.info(f"Inventory event processed: {event_data['data']['product_id']}")
        return f"Inventory processed: {event_data['data']['product_id']}"

    except Exception as exc:
        logger.error(f"Failed to process inventory event: {str(exc)}")


@shared_task
def process_notification_event(event_data):
    """Process notification Kafka event"""
    try:
        notification_data = event_data['data']
        notification_type = notification_data['type']

        if notification_type == 'email':
            send_mail(
                subject=notification_data['title'],
                message=notification_data['message'],
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification_data['email']],
            )

        logger.info(f"Notification sent: {notification_type}")
        return f"Notification processed: {notification_type}"

    except Exception as exc:
        logger.error(f"Failed to process notification event: {str(exc)}")
