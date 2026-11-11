import uuid
from decimal import Decimal
from django.db import models
from orders.models import PrintOrder
from core.models import User


class Payment(models.Model):
    class Status(models.TextChoices):
        CREATED = 'CREATED', 'Created / Initiated'
        AUTHORIZED = 'AUTHORIZED', 'Authorized'
        CAPTURED = 'CAPTURED', 'Captured / Verified'
        FAILED = 'FAILED', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(PrintOrder, on_delete=models.CASCADE, related_name='payments')
    gateway_order_id = models.CharField(max_length=100, db_index=True)
    gateway_payment_id = models.CharField(max_length=100, blank=True, db_index=True)
    gateway_signature = models.CharField(max_length=255, blank=True)
    gateway_name = models.CharField(max_length=50, default='RAZORPAY_SANDBOX')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=10, default='INR')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED)
    idempotency_key = models.CharField(max_length=128, unique=True, db_index=True)
    raw_response = models.JSONField(default=dict)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.gateway_payment_id or self.gateway_order_id} - {self.status} (INR {self.amount})"


class Refund(models.Model):
    class Status(models.TextChoices):
        INITIATED = 'INITIATED', 'Initiated'
        PROCESSED = 'PROCESSED', 'Processed / Refunded'
        FAILED = 'FAILED', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    gateway_refund_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INITIATED)
    authorized_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Refund INR {self.amount} for {self.payment} [{self.status}]"
