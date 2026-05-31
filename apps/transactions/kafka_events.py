"""
Kafka Producer & Consumer for Event-Driven Architecture
Handles all event publishing and consumption with reliability guarantees
"""

import json
import logging
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


# ==================== KAFKA PRODUCER ====================
class KafkaEventProducer:
    """Publishes events to Kafka topics"""

    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BROKER_URL,
            security_protocol=settings.KAFKA_SECURITY_PROTOCOL,
            value_serializer=lambda v: json.dumps(v, cls=DjangoJSONEncoder).encode('utf-8'),
            acks='all',  # Wait for all replicas
            retries=3,
            max_in_flight_requests_per_connection=1,  # Ensure ordering
        )

    def publish_order_created(self, order_data):
        """Publish order-created event"""
        event = {
            'event_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'ORDER_CREATED',
            'data': order_data,
            'idempotency_key': str(order_data['id']),  # For idempotency
        }

        try:
            future = self.producer.send(
                settings.KAFKA_TOPICS['ORDER_CREATED'],
                value=event,
                key=str(order_data['id']).encode('utf-8')  # Partition by order ID
            )

            record_metadata = future.get(timeout=10)
            logger.info(f"Order event published: {event['event_id']} to partition {record_metadata.partition}")
            return event['event_id']

        except KafkaError as e:
            logger.error(f"Failed to publish order event: {str(e)}")
            raise

    def publish_payment_processed(self, transaction_data):
        """Publish payment-processed event"""
        event = {
            'event_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'PAYMENT_PROCESSED',
            'data': transaction_data,
            'idempotency_key': str(transaction_data['transaction_id']),
        }

        try:
            future = self.producer.send(
                settings.KAFKA_TOPICS['PAYMENT_PROCESSED'],
                value=event,
                key=str(transaction_data['order_id']).encode('utf-8')
            )
            record_metadata = future.get(timeout=10)
            logger.info(f"Payment event published: {event['event_id']}")
            return event['event_id']

        except KafkaError as e:
            logger.error(f"Failed to publish payment event: {str(e)}")
            raise

    def publish_inventory_updated(self, inventory_data):
        """Publish inventory-updated event"""
        event = {
            'event_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'INVENTORY_UPDATED',
            'data': inventory_data,
            'idempotency_key': str(inventory_data['product_id']),
        }

        try:
            future = self.producer.send(
                settings.KAFKA_TOPICS['INVENTORY_UPDATED'],
                value=event,
                key=str(inventory_data['product_id']).encode('utf-8')
            )
            record_metadata = future.get(timeout=10)
            logger.info(f"Inventory event published: {event['event_id']}")
            return event['event_id']

        except KafkaError as e:
            logger.error(f"Failed to publish inventory event: {str(e)}")
            raise

    def publish_notification_event(self, notification_data):
        """Publish notification event"""
        event = {
            'event_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'NOTIFICATION',
            'data': notification_data,
        }

        try:
            future = self.producer.send(
                settings.KAFKA_TOPICS['NOTIFICATION_EVENTS'],
                value=event,
                key=str(notification_data.get('user_id', 'system')).encode('utf-8')
            )
            record_metadata = future.get(timeout=10)
            logger.info(f"Notification event published: {event['event_id']}")
            return event['event_id']

        except KafkaError as e:
            logger.error(f"Failed to publish notification event: {str(e)}")
            raise

    def close(self):
        """Close producer connection"""
        self.producer.close()


# ==================== KAFKA CONSUMER ====================
class KafkaEventConsumer:
    """Consumes events from Kafka topics"""

    def __init__(self, topic, group_id, auto_offset_reset='earliest'):
        self.topic = topic
        self.group_id = group_id
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=settings.KAFKA_BROKER_URL,
            security_protocol=settings.KAFKA_SECURITY_PROTOCOL,
            group_id=group_id,
            auto_offset_reset=auto_offset_reset,
            enable_auto_commit=True,
            max_poll_records=100,
            session_timeout_ms=30000,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        )

    def consume_and_process(self, process_func, max_messages=None):
        """
        Consume messages and process with given function
        process_func should be idempotent
        """
        messages_processed = 0

        try:
            for message in self.consumer:
                try:
                    logger.info(f"Processing message from {self.topic}: {message.offset}")
                    process_func(message.value)
                    messages_processed += 1

                    if max_messages and messages_processed >= max_messages:
                        break

                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}, sending to DLQ")
                    # Send to DLQ
                    self._send_to_dlq(message.value, str(e))

        except KeyboardInterrupt:
            logger.info(f"Consumer interrupted after processing {messages_processed} messages")
        finally:
            self.consumer.close()

    def _send_to_dlq(self, message, error):
        """Send failed message to Dead Letter Queue"""
        dlq_producer = KafkaEventProducer()
        dlq_event = {
            'original_message': message,
            'error': error,
            'failed_at': datetime.utcnow().isoformat(),
        }

        try:
            dlq_producer.producer.send(
                settings.KAFKA_TOPICS['TRANSACTION_DLQ'],
                value=dlq_event
            )
            logger.info("Message sent to DLQ")
        except Exception as e:
            logger.error(f"Failed to send message to DLQ: {str(e)}")
        finally:
            dlq_producer.close()

    def close(self):
        """Close consumer connection"""
        self.consumer.close()


# ==================== SINGLETON PRODUCER ====================
_producer_instance = None


def get_kafka_producer():
    """Get or create singleton Kafka producer"""
    global _producer_instance
    if _producer_instance is None:
        _producer_instance = KafkaEventProducer()
    return _producer_instance


# ==================== HELPER FUNCTIONS ====================
def publish_order_created_event(order):
    """Publish order created event"""
    producer = get_kafka_producer()
    order_data = {
        'id': str(order.id),
        'user_id': str(order.user.id),
        'total_amount': str(order.total_amount),
        'status': order.status,
        'items': [
            {
                'product_id': str(item.product_id),
                'quantity': item.quantity,
                'unit_price': str(item.unit_price),
            }
            for item in order.order_items.all()
        ],
        'created_at': order.created_at.isoformat(),
    }
    return producer.publish_order_created(order_data)


def publish_payment_processed_event(transaction):
    """Publish payment processed event"""
    producer = get_kafka_producer()
    transaction_data = {
        'transaction_id': str(transaction.id),
        'order_id': str(transaction.order_id),
        'user_id': str(transaction.order.user_id),
        'amount': str(transaction.amount),
        'status': transaction.status,
        'payment_method': transaction.payment_method,
        'processed_at': transaction.processed_at.isoformat() if transaction.processed_at else None,
    }
    return producer.publish_payment_processed(transaction_data)


def publish_inventory_updated_event(product, quantity_change):
    """Publish inventory updated event"""
    producer = get_kafka_producer()
    inventory_data = {
        'product_id': str(product.id),
        'product_name': product.product_name,
        'quantity_change': quantity_change,
        'new_stock_level': product.stock_quantity,
        'availability_status': product.availability_status,
    }
    return producer.publish_inventory_updated(inventory_data)


def publish_notification_event(user_id, notification_type, title, message):
    """Publish notification event"""
    producer = get_kafka_producer()
    notification_data = {
        'user_id': str(user_id),
        'type': notification_type,  # email, sms, push
        'title': title,
        'message': message,
    }
    return producer.publish_notification_event(notification_data)
