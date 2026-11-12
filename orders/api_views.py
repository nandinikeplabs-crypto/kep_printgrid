import hashlib
import uuid
import secrets
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from core.models import Shop, AuditLog
from printers.models import Printer
from .models import PrintDocument, PrintPreference, PricingRule, PrintOrder, PrintJob


def resolve_shop(identifier):
    """Resolves shop by either unique shop_code (e.g. KEP10001) or slug."""
    if not identifier:
        return None
    return Shop.objects.filter(Q(shop_code__iexact=identifier) | Q(slug__iexact=identifier)).first()


class QuoteAPIView(APIView):
    """
    Computes an exact, transparent price quote before checkout.
    Never silently inflates agreed prices.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        shop_slug = request.data.get('shop_slug')
        shop = resolve_shop(shop_slug)
        if not shop:
            return Response({'error': f"Shop '{shop_slug}' not found."}, status=status.HTTP_404_NOT_FOUND)

        pricing = PricingRule.objects.filter(shop=shop, is_active=True).first()
        if not pricing:
            pricing = PricingRule.objects.create(shop=shop)

        raw_page_count = int(request.data.get('page_count', 1))
        color_mode = request.data.get('color_mode', 'BW')
        duplex_mode = request.data.get('duplex_mode', 'SINGLE')
        paper_size = request.data.get('paper_size', 'A4')
        copies = int(request.data.get('copies', 1))
        finishing_service = request.data.get('finishing_service', 'NONE')
        page_range_type = request.data.get('page_range_type', 'ALL')
        page_range_selection = request.data.get('page_range_selection', '').strip()

        # Page count resolution
        if page_range_type == 'CUSTOM' and page_range_selection:
            # Parse selected pages like "1-3, 5"
            selected_count = 0
            for part in page_range_selection.split(','):
                part = part.strip()
                if '-' in part:
                    s, e = part.split('-', 1)
                    if s.isdigit() and e.isdigit():
                        selected_count += max(0, int(e) - int(s) + 1)
                elif part.isdigit():
                    selected_count += 1
            effective_pages = max(1, min(selected_count, raw_page_count))
        else:
            effective_pages = max(1, raw_page_count)

        # Temporary preference instance for calculation
        pref = PrintPreference(
            color_mode=color_mode,
            duplex_mode=duplex_mode,
            paper_size=paper_size,
            copies=copies,
            finishing_service=finishing_service,
            page_range_type=page_range_type,
            page_range_selection=page_range_selection,
            total_calculated_pages=effective_pages
        )

        quote = pricing.calculate_price(pref, effective_pages)
        return Response(quote)


class UploadEncryptedDocumentAPIView(APIView):
    """
    Receives the browser-encrypted PDF ciphertext.
    The cloud server receives only ciphertext and wrapped key bundle.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        shop_slug = request.data.get('shop_slug')
        shop = resolve_shop(shop_slug)
        if not shop:
            return Response({'error': f"Shop '{shop_slug}' not found."}, status=status.HTTP_404_NOT_FOUND)

        if not shop.is_accepting_orders:
            return Response(
                {'error': shop.pause_message},
                status=status.HTTP_400_BAD_REQUEST
            )

        encrypted_file = request.FILES.get('encrypted_file')
        if not encrypted_file:
            return Response({'error': 'Missing encrypted file payload.'}, status=status.HTTP_400_BAD_REQUEST)

        # Read content and compute hash to verify integrity
        file_bytes = encrypted_file.read()
        computed_hash = hashlib.sha256(file_bytes).hexdigest()
        encrypted_file.seek(0)

        encrypted_key_bundle = request.data.get('encrypted_key_bundle', '').strip()
        encryption_iv = request.data.get('encryption_iv', '').strip()
        encryption_tag = request.data.get('encryption_tag', '').strip()
        detected_page_count = int(request.data.get('detected_page_count', 1))
        original_filename = request.data.get('original_filename', 'document.pdf').strip()

        if not encrypted_key_bundle or not encryption_iv:
            return Response(
                {'error': 'Missing client-side encryption metadata (key bundle or IV).'},
                status=status.HTTP_400_BAD_REQUEST
            )

        document = PrintDocument.objects.create(
            shop=shop,
            original_filename=original_filename,
            file_hash_sha256=computed_hash,
            encrypted_file=encrypted_file,
            encrypted_file_size=len(file_bytes),
            encrypted_key_bundle=encrypted_key_bundle,
            encryption_iv=encryption_iv,
            encryption_tag=encryption_tag,
            detected_page_count=detected_page_count
        )

        return Response({
            'document_id': str(document.id),
            'filename': document.original_filename,
            'size': document.encrypted_file_size,
            'detected_page_count': document.detected_page_count,
            'sha256': document.file_hash_sha256,
        }, status=status.HTTP_201_CREATED)


class CreatePrintOrderAPIView(APIView):
    """
    Creates an order awaiting payment.
    Ensures idempotency and price integrity.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        shop_slug = request.data.get('shop_slug')
        shop = resolve_shop(shop_slug)
        if not shop:
            return Response({'error': f"Shop '{shop_slug}' not found."}, status=status.HTTP_404_NOT_FOUND)

        if not shop.is_accepting_orders:
            return Response({'error': shop.pause_message}, status=status.HTTP_400_BAD_REQUEST)

        document_id = request.data.get('document_id')
        document = get_object_or_404(PrintDocument, id=document_id, shop=shop)

        # Check idempotency
        idempotency_key = request.data.get('idempotency_key') or f"idemp_{uuid.uuid4().hex}"
        existing_order = PrintOrder.objects.filter(idempotency_key=idempotency_key).first()
        if existing_order:
            return Response({
                'order_number': existing_order.order_number,
                'total_amount': str(existing_order.total_amount),
                'status': existing_order.status,
                'pricing_breakdown': existing_order.pricing_breakdown
            })

        prefs_data = request.data.get('preferences', {})
        color_mode = prefs_data.get('color_mode', 'BW')
        duplex_mode = prefs_data.get('duplex_mode', 'SINGLE')
        paper_size = prefs_data.get('paper_size', 'A4')
        copies = max(1, int(prefs_data.get('copies', 1)))
        finishing_service = prefs_data.get('finishing_service', 'NONE')
        page_range_type = prefs_data.get('page_range_type', 'ALL')
        page_range_selection = prefs_data.get('page_range_selection', '').strip()

        # Calculate pages
        num_pages = document.detected_page_count
        if page_range_type == 'CUSTOM' and page_range_selection:
            selected_count = 0
            for part in page_range_selection.split(','):
                part = part.strip()
                if '-' in part:
                    s, e = part.split('-', 1)
                    if s.isdigit() and e.isdigit():
                        selected_count += max(0, int(e) - int(s) + 1)
                elif part.isdigit():
                    selected_count += 1
            num_pages = max(1, min(selected_count, document.detected_page_count))

        preference = PrintPreference.objects.create(
            color_mode=color_mode,
            duplex_mode=duplex_mode,
            paper_size=paper_size,
            copies=copies,
            finishing_service=finishing_service,
            page_range_type=page_range_type,
            page_range_selection=page_range_selection,
            total_calculated_pages=num_pages
        )

        pricing = PricingRule.objects.filter(shop=shop, is_active=True).first()
        if not pricing:
            pricing = PricingRule.objects.create(shop=shop)

        breakdown = pricing.calculate_price(preference, num_pages)
        total_amount = Decimal(str(breakdown['total_amount']))

        # Generate unique order number (e.g. ORD-20261111-9284)
        date_str = timezone.now().strftime('%Y%m%d')
        random_suffix = secrets.token_hex(2).upper()
        order_number = f"ORD-{date_str}-{random_suffix}"
        while PrintOrder.objects.filter(order_number=order_number).exists():
            order_number = f"ORD-{date_str}-{secrets.token_hex(2).upper()}"

        customer_name = request.data.get('customer_name', 'Customer').strip() or 'Customer'
        customer_phone = request.data.get('customer_phone', '').strip()

        order = PrintOrder.objects.create(
            order_number=order_number,
            shop=shop,
            qr_code=getattr(shop, 'qr_code', None),
            customer_name=customer_name,
            customer_phone=customer_phone,
            document=document,
            preference=preference,
            status=PrintOrder.Status.AWAITING_PAYMENT,
            total_amount=total_amount,
            pricing_breakdown=breakdown,
            idempotency_key=idempotency_key
        )

        AuditLog.objects.create(
            shop=shop,
            action='PRINT_ORDER_CREATED',
            resource_type='PrintOrder',
            resource_id=str(order.id),
            details={'order_number': order_number, 'total_amount': str(total_amount)}
        )

        return Response({
            'order_number': order.order_number,
            'total_amount': str(order.total_amount),
            'pricing_breakdown': breakdown,
            'status': order.status,
            'currency': 'INR',
        }, status=status.HTTP_201_CREATED)


class OrderStatusAPIView(APIView):
    """
    Returns live order and print job status.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, order_number):
        order = get_object_or_404(
            PrintOrder.objects.select_related('shop', 'document', 'preference', 'print_job', 'print_job__printer'),
            order_number=order_number
        )
        job = getattr(order, 'print_job', None)

        # Self-healing auto-spool: If order is paid but waiting for spooler, auto-spool immediately
        if order.status in [
            PrintOrder.Status.PAYMENT_VERIFIED,
            PrintOrder.Status.QUEUED,
            PrintOrder.Status.ASSIGNED,
            PrintOrder.Status.SENT_TO_PRINTER,
            PrintOrder.Status.PRINTING,
        ] and job:
            try:
                from payments.views import auto_spool_paid_order
                auto_spool_paid_order(job)
                order.refresh_from_db()
                job.refresh_from_db()
            except Exception as e:
                logger.warning(f"OrderStatusAPIView auto-spool notice: {e}")

        return Response({
            'order_number': order.order_number,
            'shop_name': order.shop.name,
            'status': order.status,
            'status_display': order.get_status_display(),
            'total_amount': str(order.total_amount),
            'currency': 'INR',
            'created_at': order.created_at.isoformat(),
            'job_status': job.status if job else None,
            'printer_name': job.printer.name if job and job.printer else None,
            'failure_reason': job.failure_reason if job else None,
            'is_completed': order.status == PrintOrder.Status.COMPLETED,
        })
