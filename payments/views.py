import json
import logging
from decimal import Decimal
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db import transaction
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from core.models import AuditLog
from core.decorators import staff_or_owner_required, get_user_shop
from orders.models import PrintOrder, PrintJob
from printers.services.routing_service import RoutingService
from .models import Payment, Refund
from .services.gateway_adapter import get_payment_gateway, RazorpaySandboxAdapter

logger = logging.getLogger(__name__)


class CreatePaymentOrderAPIView(APIView):
    """
    Creates a server-side payment order via the configured gateway adapter.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        order_number = request.data.get('order_number')
        order = get_object_or_404(PrintOrder, order_number=order_number)

        if order.status not in [PrintOrder.Status.AWAITING_PAYMENT, PrintOrder.Status.UPLOADED]:
            return Response(
                {'error': f"Order is already in '{order.get_status_display()}' state."},
                status=status.HTTP_400_BAD_REQUEST
            )

        gateway = get_payment_gateway()
        order_payload = gateway.create_order(
            amount=order.total_amount,
            currency='INR',
            receipt=order.order_number,
            notes={
                'order_number': order.order_number,
                'shop_id': str(order.shop.id),
                'shop_name': order.shop.name
            }
        )

        idempotency_key = f"pay_{order.order_number}_{order_payload['id']}"

        # Create or retrieve Payment model record
        payment, _ = Payment.objects.get_or_create(
            order=order,
            gateway_order_id=order_payload['id'],
            defaults={
                'amount': order.total_amount,
                'currency': 'INR',
                'status': Payment.Status.CREATED,
                'gateway_name': type(gateway).__name__,
                'idempotency_key': idempotency_key,
                'raw_response': order_payload
            }
        )

        resp_data = {
            'gateway_order_id': order_payload['id'],
            'amount_paise': order_payload['amount'],
            'currency': order_payload['currency'],
            'key_id': order_payload.get('key_id', 'rzp_test'),
            'order_number': order.order_number,
            'is_sandbox': isinstance(gateway, RazorpaySandboxAdapter),
        }

        # In sandbox mode, provide the helper signature for frontend test runner
        if isinstance(gateway, RazorpaySandboxAdapter):
            mock_payment_id = f"pay_test_{order.order_number.replace('-', '_')}"
            expected_sig = gateway.generate_expected_signature(order_payload['id'], mock_payment_id)
            resp_data['sandbox_helper'] = {
                'sample_payment_id': mock_payment_id,
                'sample_signature': expected_sig,
            }

        return Response(resp_data, status=status.HTTP_201_CREATED)


class VerifyPaymentAPIView(APIView):
    """
    Verifies payment signature on the backend.
    Never trusts a frontend payment-success message without cryptographic verification.
    Releases printing job only on verified payment.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        gateway_order_id = request.data.get('gateway_order_id')
        gateway_payment_id = request.data.get('gateway_payment_id')
        gateway_signature = request.data.get('gateway_signature')

        if not gateway_order_id or not gateway_payment_id or not gateway_signature:
            return Response(
                {'error': 'Missing payment verification credentials.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        payment = get_object_or_404(Payment, gateway_order_id=gateway_order_id)
        order = payment.order

        gateway = get_payment_gateway()
        is_valid = gateway.verify_payment_signature(
            order_id=gateway_order_id,
            payment_id=gateway_payment_id,
            signature=gateway_signature
        )

        if not is_valid:
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=['status', 'updated_at'])
            return Response(
                {'error': 'Cryptographic payment signature verification failed. Job will NOT be released.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            # Check idempotency: avoid double processing if webhook or repeat hit
            if payment.status == Payment.Status.CAPTURED:
                return Response({
                    'status': 'already_processed',
                    'order_number': order.order_number,
                    'redirect_url': f"/orders/track/{order.order_number}/"
                })

            payment.gateway_payment_id = gateway_payment_id
            payment.gateway_signature = gateway_signature
            payment.status = Payment.Status.CAPTURED
            payment.verified_at = timezone.now()
            payment.save()

            order.status = PrintOrder.Status.PAYMENT_VERIFIED
            order.save(update_fields=['status', 'updated_at'])

            # Route and dispatch exactly one authorized print job
            job = RoutingService.route_paid_order(order)

            AuditLog.objects.create(
                shop=order.shop,
                action='PAYMENT_VERIFIED',
                resource_type='Payment',
                resource_id=str(payment.id),
                details={
                    'order_number': order.order_number,
                    'payment_id': gateway_payment_id,
                    'amount': str(payment.amount),
                    'job_status': job.status,
                    'printer': job.printer.name if job.printer else 'QUEUED'
                }
            )

        return Response({
            'status': 'verified',
            'order_number': order.order_number,
            'job_status': job.status,
            'redirect_url': f"/orders/track/{order.order_number}/"
        })


class PaymentWebhookAPIView(APIView):
    """
    Handles payment provider webhooks with signature verification.
    Prevents duplicate releases using transaction locking and idempotency.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        signature = request.headers.get('X-Razorpay-Signature')
        gateway = get_payment_gateway()

        if not gateway.verify_webhook_signature(request.body, signature):
            return Response({'error': 'Invalid webhook signature.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payload = json.loads(request.body.decode('utf-8'))
            event = payload.get('event')

            if event == 'payment.captured':
                payment_entity = payload.get('payload', {}).get('payment', {}).get('entity', {})
                gateway_order_id = payment_entity.get('order_id')
                gateway_payment_id = payment_entity.get('id')

                payment = Payment.objects.filter(gateway_order_id=gateway_order_id).first()
                if payment and payment.status != Payment.Status.CAPTURED:
                    with transaction.atomic():
                        payment.gateway_payment_id = gateway_payment_id
                        payment.status = Payment.Status.CAPTURED
                        payment.verified_at = timezone.now()
                        payment.save()

                        order = payment.order
                        order.status = PrintOrder.Status.PAYMENT_VERIFIED
                        order.save()

                        RoutingService.route_paid_order(order)

            return Response({'status': 'webhook_received'})
        except Exception as e:
            logger.exception("Error processing payment webhook")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@staff_or_owner_required
def initiate_refund_view(request, order_number):
    """
    Issues an authorized refund for cancelled or failed print orders.
    """
    shop = get_user_shop(request.user)
    order = get_object_or_404(PrintOrder, shop=shop, order_number=order_number)
    payment = order.payments.filter(status=Payment.Status.CAPTURED).first()

    if not payment:
        messages.error(request, "No captured payment found to refund for this order.")
        return redirect('orders:order_detail', order_number=order_number)

    reason = request.POST.get('reason', 'Customer requested cancellation or hardware failure')

    gateway = get_payment_gateway()
    try:
        refund_data = gateway.initiate_refund(
            payment_id=payment.gateway_payment_id or payment.gateway_order_id,
            amount=payment.amount,
            reason=reason
        )

        with transaction.atomic():
            Refund.objects.create(
                payment=payment,
                amount=payment.amount,
                reason=reason,
                gateway_refund_id=refund_data.get('id', ''),
                status=Refund.Status.PROCESSED,
                authorized_by=request.user
            )

            order.status = PrintOrder.Status.REFUNDED
            order.save()

            if hasattr(order, 'print_job'):
                job = order.print_job
                job.status = PrintJob.Status.FAILED
                job.failure_reason = f"Refunded: {reason}"
                job.save()

            AuditLog.objects.create(
                shop=shop,
                user=request.user,
                action='PAYMENT_REFUNDED',
                resource_type='Refund',
                resource_id=refund_data.get('id', ''),
                details={
                    'order_number': order.order_number,
                    'amount': str(payment.amount),
                    'reason': reason
                }
            )

        messages.success(request, f"Refund of INR {payment.amount} has been processed successfully.")
    except Exception as e:
        messages.error(request, f"Refund processing failed: {str(e)}")

    return redirect('orders:order_detail', order_number=order_number)
