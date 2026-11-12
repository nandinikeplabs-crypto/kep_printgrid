import os
import sys
import django
import time

# Initialize Django environment
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kep_printgrid.settings")
django.setup()

from decimal import Decimal
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import Shop, User
from orders.models import PrintOrder, PrintDocument, PrintPreference, PricingRule, PrintJob
from payments.models import Payment
from payments.services.gateway_adapter import get_payment_gateway
from printers.models import Printer
from printers.services.routing_service import RoutingService


def run_customer_terminal_demo():
    print("=" * 70)
    print("      KEP PRINTGRID - CUSTOMER USER WORKFLOW SIMULATION (VS CODE)    ")
    print("=" * 70)

    # 1. Customer Scans QR Code
    shop = Shop.objects.filter(slug="metro-xerox").first()
    if not shop:
        print("[!] Demo shop 'metro-xerox' not found. Run 'python manage.py seed_demo_data' first.")
        return

    print(f"\n[STEP 1] Customer scans shop QR code with phone...")
    print(f"  -> Connected to Shop: {shop.name}")
    print(f"  -> Location: {shop.address}")
    print(f"  -> Permanent Order URL: {shop.order_page_url}")
    print(f"  -> Shop Status: {'ACCEPTING ORDERS' if shop.is_accepting_orders else 'PAUSED'}")

    # 2. Document Selection & Browser-Side Prep
    print(f"\n[STEP 2] Customer prepares document via GetFilePilot tools...")
    filename = "Computer_Networks_Lab_Report.pdf"
    raw_pages = 4
    print(f"  -> File: {filename}")
    print(f"  -> Total Pages: {raw_pages}")
    print(f"  -> Client-Side Encryption: AES-256-GCM + Shop RSA-2048 Wrapping")

    doc = PrintDocument.objects.create(
        shop=shop,
        original_filename=filename,
        file_hash_sha256="9a2f64c7810e74b321a5b6c8d7e9f01234567890abcdef1234567890abcdef12",
        encrypted_file=SimpleUploadedFile("report.enc", b"encrypted_pdf_ciphertext_sample_stream"),
        encrypted_file_size=2048,
        encrypted_key_bundle="sample_rsa_wrapped_aes_session_key_bundle",
        encryption_iv="sample_aes_gcm_iv",
        detected_page_count=raw_pages
    )
    print(f"  -> Document ID Created: {doc.id}")

    # 3. Preference Selection
    print(f"\n[STEP 3] Customer chooses printing preferences...")
    color_mode = "BW"
    duplex_mode = "DOUBLE"
    paper_size = "A4"
    copies = 2
    finishing = "CORNER_STAPLE"

    print(f"  -> Color: {color_mode}")
    print(f"  -> Sides: {duplex_mode} (Back-to-Back)")
    print(f"  -> Paper: {paper_size}")
    print(f"  -> Copies: {copies}")
    print(f"  -> Finishing: {finishing}")

    pref = PrintPreference.objects.create(
        color_mode=color_mode,
        duplex_mode=duplex_mode,
        paper_size=paper_size,
        copies=copies,
        finishing_service=finishing,
        total_calculated_pages=raw_pages
    )

    # 4. Instant Price Quote Calculation
    pricing = PricingRule.objects.filter(shop=shop, is_active=True).first()
    quote = pricing.calculate_price(pref, raw_pages)

    print(f"\n[STEP 4] Dynamic Price Quote calculated from shop rates...")
    print(f"  -> Rate per sheet: Rs {quote['unit_rate']} ({quote['rate_label']})")
    print(f"  -> Physical Sheets needed: {quote['total_sheets']}")
    print(f"  -> Printing subtotal: Rs {quote['printing_subtotal']}")
    print(f"  -> Finishing service: {quote['finishing_label']} (+Rs {quote['finishing_cost']})")
    print(f"  -------------------------------------------------------------")
    print(f"  -> TOTAL PAYABLE AMOUNT: Rs {quote['total_amount']} INR")

    # 5. Order Creation
    order_num = f"ORD-DEMO-{int(time.time())}"
    cust_name = "Anand Sharma (Student)"
    cust_phone = "+91 9876543210"

    order = PrintOrder.objects.create(
        order_number=order_num,
        shop=shop,
        customer_name=cust_name,
        customer_phone=cust_phone,
        document=doc,
        preference=pref,
        status=PrintOrder.Status.AWAITING_PAYMENT,
        total_amount=Decimal(str(quote['total_amount'])),
        pricing_breakdown=quote,
        idempotency_key=f"idemp_demo_{order_num}"
    )
    print(f"\n[STEP 5] Order Created: #{order.order_number}")
    print(f"  -> Customer: {cust_name} ({cust_phone})")
    print(f"  -> Initial Status: {order.get_status_display()}")

    # 6. Payment Execution (Razorpay HMAC Verification)
    print(f"\n[STEP 6] Customer pays via Razorpay...")
    gateway = get_payment_gateway()
    pay_order = gateway.create_order(order.total_amount, 'INR', order.order_number, {})
    mock_payment_id = f"pay_test_{order.order_number}"
    signature = gateway.generate_expected_signature(pay_order['id'], mock_payment_id)

    payment = Payment.objects.create(
        order=order,
        gateway_order_id=pay_order['id'],
        gateway_payment_id=mock_payment_id,
        gateway_signature=signature,
        gateway_name="RAZORPAY_SANDBOX",
        amount=order.total_amount,
        currency="INR",
        status=Payment.Status.CAPTURED,
        idempotency_key=f"pay_idemp_{order_num}",
        verified_at=timezone.now()
    )
    order.status = PrintOrder.Status.PAYMENT_VERIFIED
    order.save()
    print(f"  -> Gateway Order ID: {pay_order['id']}")
    print(f"  -> Payment ID: {mock_payment_id}")
    print(f"  -> Signature HMAC-SHA256: {signature[:16]}... (VALIDATED)")
    print(f"  -> Payment Status: CAPTURED & VERIFIED")

    # 7. Intelligent Routing & Job Release
    print(f"\n[STEP 7] Intelligent Router selects capable copier...")
    job = RoutingService.route_paid_order(order)
    order.refresh_from_db()
    print(f"  -> Assigned Copier: {job.printer.name if job.printer else 'Queued'}")
    print(f"  -> Print Job Status: {job.get_status_display()}")
    print(f"  -> Order Status: {order.get_status_display()}")

    # 8. Real-Time Order Tracking Telemetry
    print(f"\n[STEP 8] Customer tracks live progress...")
    stages = [
        ("QUEUED", "Waiting in print queue for printer spooler..."),
        ("PRINTING", "Copier heating fuser and pulling paper sheets..."),
        ("FINISHING_IN_PROGRESS", "Stapling corner of 2 document copies..."),
        ("READY_FOR_PICKUP", "Ready at counter! Please collect your printout.")
    ]

    for st_code, st_desc in stages:
        time.sleep(0.6)
        print(f"  [>] Progress: [{st_code}] - {st_desc}")

    order.status = PrintOrder.Status.COMPLETED
    order.save()
    job.status = PrintJob.Status.PHYSICALLY_PRINTED
    job.completed_at = timezone.now()
    job.save()

    print(f"\n[COMPLETE] Order Handover finished successfully!")
    print(f"  -> Final Status: {order.get_status_display()}")
    print("=" * 70)


if __name__ == "__main__":
    run_customer_terminal_demo()
