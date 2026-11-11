import hmac
import hashlib
import json
import secrets
from decimal import Decimal
from abc import ABC, abstractmethod
from django.conf import settings


class BasePaymentGatewayAdapter(ABC):
    @abstractmethod
    def create_order(self, amount: Decimal, currency: str, receipt: str, notes: dict) -> dict:
        pass

    @abstractmethod
    def verify_payment_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        pass

    @abstractmethod
    def verify_webhook_signature(self, payload_bytes: bytes, signature: str) -> bool:
        pass

    @abstractmethod
    def initiate_refund(self, payment_id: str, amount: Decimal, reason: str) -> dict:
        pass


class RazorpaySandboxAdapter(BasePaymentGatewayAdapter):
    """
    High-fidelity Razorpay sandbox simulator.
    Provides identical API shapes, realistic IDs ('order_sandbox_...', 'pay_sandbox_...'),
    and enforces genuine HMAC-SHA256 signature verification without requiring active banking API keys.
    """
    def __init__(self):
        self.key_id = getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_kep_demo_key')
        self.key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', 'rzp_test_kep_demo_secret')
        self.webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', 'rzp_test_webhook_secret')

    def create_order(self, amount: Decimal, currency: str, receipt: str, notes: dict) -> dict:
        # Amount in paise (1 INR = 100 paise)
        amount_paise = int(amount * 100)
        gateway_order_id = f"order_{secrets.token_hex(8)}"
        return {
            'id': gateway_order_id,
            'entity': 'order',
            'amount': amount_paise,
            'amount_paid': 0,
            'amount_due': amount_paise,
            'currency': currency,
            'receipt': receipt,
            'status': 'created',
            'notes': notes,
            'key_id': self.key_id,
        }

    def generate_expected_signature(self, order_id: str, payment_id: str) -> str:
        msg = f"{order_id}|{payment_id}".encode('utf-8')
        return hmac.new(self.key_secret.encode('utf-8'), msg, hashlib.sha256).hexdigest()

    def verify_payment_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        if not signature or not order_id or not payment_id:
            return False
        expected = self.generate_expected_signature(order_id, payment_id)
        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected, signature)

    def verify_webhook_signature(self, payload_bytes: bytes, signature: str) -> bool:
        if not signature:
            return False
        expected = hmac.new(self.webhook_secret.encode('utf-8'), payload_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def initiate_refund(self, payment_id: str, amount: Decimal, reason: str) -> dict:
        refund_id = f"rfnd_{secrets.token_hex(8)}"
        return {
            'id': refund_id,
            'entity': 'refund',
            'amount': int(amount * 100),
            'currency': 'INR',
            'payment_id': payment_id,
            'status': 'processed',
            'notes': {'reason': reason}
        }


class RazorpayLiveAdapter(BasePaymentGatewayAdapter):
    """
    Live Razorpay API Integration using standard HTTP requests.
    """
    def __init__(self):
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self.webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
        self.base_url = "https://api.razorpay.com/v1"

    def create_order(self, amount: Decimal, currency: str, receipt: str, notes: dict) -> dict:
        import requests
        amount_paise = int(amount * 100)
        resp = requests.post(
            f"{self.base_url}/orders",
            auth=(self.key_id, self.key_secret),
            json={
                'amount': amount_paise,
                'currency': currency,
                'receipt': receipt,
                'notes': notes,
            },
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        data['key_id'] = self.key_id
        return data

    def verify_payment_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        msg = f"{order_id}|{payment_id}".encode('utf-8')
        expected = hmac.new(self.key_secret.encode('utf-8'), msg, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def verify_webhook_signature(self, payload_bytes: bytes, signature: str) -> bool:
        expected = hmac.new(self.webhook_secret.encode('utf-8'), payload_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def initiate_refund(self, payment_id: str, amount: Decimal, reason: str) -> dict:
        import requests
        amount_paise = int(amount * 100)
        resp = requests.post(
            f"{self.base_url}/payments/{payment_id}/refund",
            auth=(self.key_id, self.key_secret),
            json={'amount': amount_paise, 'notes': {'reason': reason}},
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()


def get_payment_gateway() -> BasePaymentGatewayAdapter:
    """
    Returns the appropriate payment gateway adapter based on configuration.
    """
    sandbox_mode = getattr(settings, 'PAYMENT_SANDBOX_MODE', True)
    if sandbox_mode or not getattr(settings, 'RAZORPAY_KEY_ID', None) or 'sample' in settings.RAZORPAY_KEY_ID:
        return RazorpaySandboxAdapter()
    return RazorpayLiveAdapter()
