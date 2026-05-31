"""Mock payment gateway for testing"""
import random
import uuid
from datetime import datetime


class MockPaymentGateway:
    """Mock payment gateway simulator"""

    PROVIDER_SUCCESS_RATE = 0.95  # 95% success rate

    @staticmethod
    def generate_transaction_id():
        """Generate unique transaction ID"""
        return f"TXN-{uuid.uuid4().hex[:12].upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    @staticmethod
    def validate_amount(amount):
        """Validate amount"""
        try:
            amount_float = float(amount)
            if amount_float <= 0:
                return False, "Amount must be positive"
            if amount_float > 1000000:  # Max 10 lakhs
                return False, "Amount exceeds maximum limit"
            return True, None
        except (ValueError, TypeError):
            return False, "Invalid amount"

    @staticmethod
    def process_payment(amount, transaction_id):
        """
        Process mock payment
        Returns: (success: bool, message: str)
        """
        # Validate amount
        valid, error = MockPaymentGateway.validate_amount(amount)
        if not valid:
            return False, error

        # Simulate random success/failure based on configured rate
        if random.random() < MockPaymentGateway.PROVIDER_SUCCESS_RATE:
            # Successful payment
            return True, {
                'status': 'SUCCESS',
                'transaction_id': transaction_id,
                'amount': amount,
                'timestamp': datetime.now().isoformat(),
                'reference_number': f"REF-{uuid.uuid4().hex[:8].upper()}",
            }
        else:
            # Failed payment
            failure_reasons = [
                'Insufficient funds',
                'Card declined',
                'Expired card',
                'Invalid CVV',
                'Gateway timeout',
                'Session expired',
            ]
            return False, random.choice(failure_reasons)

    @staticmethod
    def verify_payment(transaction_id):
        """Verify payment status"""
        # In mock, we can check database
        from .models import Transaction
        try:
            transaction = Transaction.objects.get(transaction_id=transaction_id)
            return transaction.status == 'COMPLETED'
        except Transaction.DoesNotExist:
            return False

    @staticmethod
    def refund_payment(transaction_id, amount):
        """Refund payment"""
        return True, f"Refund of {amount} initiated for {transaction_id}"


def process_mock_payment(amount, transaction_id):
    """
    Process payment using mock gateway
    Returns: (success: bool, response: dict or str)
    """
    gateway = MockPaymentGateway()
    success, response = gateway.process_payment(amount, transaction_id)

    if success:
        return True, "Payment successful"
    else:
        return False, response
