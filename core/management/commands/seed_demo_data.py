import io
import os
import secrets
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from core.models import User, Shop, ShopStaff
from core.services.qr_service import generate_shop_qr_code
from printers.models import Printer, PrinterCapability, PrinterAssignment, Connector
from orders.models import PricingRule, PrintDocument, PrintPreference, PrintOrder, PrintJob, PrintJobAttempt
from payments.models import Payment
from connector.crypto_manager import ConnectorCryptoManager


class Command(BaseCommand):
    help = "Seeds demo print shop, staff, printers, pricing, and sample orders for development."

    def handle(self, *args, **options):
        self.stdout.write("Seeding KEP PrintGrid demo data...")

        # 1. Shop Owner
        owner, created = User.objects.get_or_create(
            username="metro_owner",
            defaults={
                "email": "owner@metroprint.example",
                "first_name": "Ramesh",
                "last_name": "Kumar",
                "role": User.Role.OWNER,
                "phone_number": "+91 9876543210"
            }
        )
        if created:
            owner.set_password("MetroPrint2026!")
            owner.save()
            self.stdout.write(self.style.SUCCESS(f"Created Owner: owner@metroprint.example / MetroPrint2026!"))

        # 2. Shop
        crypto = ConnectorCryptoManager()
        shop, s_created = Shop.objects.get_or_create(
            slug="metro-xerox",
            defaults={
                "name": "Metro Xerox & Multi-Service Hub",
                "owner": owner,
                "phone": "+91 9876543210",
                "email": "owner@metroprint.example",
                "address": "Shop No. 4, College Road, Opp. University Gate",
                "is_accepting_orders": True,
                "connector_auth_token": "metro_demo_auth_token_991823719827391827",
                "connector_public_key": crypto.get_public_key_pem(),
                "connector_last_seen": timezone.now(),
            }
        )
        if s_created:
            generate_shop_qr_code(shop)
            self.stdout.write(self.style.SUCCESS(f"Created Shop: {shop.name} (Slug: {shop.slug})"))

        # 3. Staff User
        staff_user, st_created = User.objects.get_or_create(
            username="metro_staff",
            defaults={
                "email": "staff@metroprint.example",
                "first_name": "Suresh",
                "last_name": "Verma",
                "role": User.Role.STAFF,
                "phone_number": "+91 9123456789"
            }
        )
        if st_created:
            staff_user.set_password("StaffPass2026!")
            staff_user.save()
            ShopStaff.objects.create(
                shop=shop,
                user=staff_user,
                can_manage_printers=True,
                can_authorize_retries=True,
                can_manage_pricing=False
            )
            self.stdout.write(self.style.SUCCESS(f"Created Staff: staff@metroprint.example / StaffPass2026!"))

        # 4. Pricing Rules
        PricingRule.objects.get_or_create(
            shop=shop,
            defaults={
                "bw_single_rate": Decimal("2.00"),
                "bw_double_rate": Decimal("3.50"),
                "color_single_rate": Decimal("10.00"),
                "color_double_rate": Decimal("18.00"),
                "a3_bw_rate": Decimal("5.00"),
                "a3_color_rate": Decimal("20.00"),
                "is_active": True
            }
        )

        # 5. Connected Printers
        p1, _ = Printer.objects.get_or_create(
            shop=shop,
            system_printer_name="HP_LaserJet_Pro_M428fdw",
            defaults={
                "name": "HP LaserJet Pro M428fdw (Counter 1 - Fast B&W)",
                "model_name": "HP M428fdw",
                "is_active": True,
                "is_online": True,
                "is_default": True,
                "handles_bw": True,
                "handles_color": False,
                "last_status_message": "Ready"
            }
        )
        PrinterCapability.objects.get_or_create(
            printer=p1,
            defaults={
                "supports_bw": True,
                "supports_color": False,
                "supports_duplex": True,
                "supported_paper_sizes": ["A4", "LETTER"],
                "dpi": 1200
            }
        )

        p2, _ = Printer.objects.get_or_create(
            shop=shop,
            system_printer_name="Canon_imageRUNNER_ADVANCE_C3530i",
            defaults={
                "name": "Canon imageRUNNER ADVANCE C3530i (Color & A3)",
                "model_name": "Canon iR ADV C3530i",
                "is_active": True,
                "is_online": True,
                "is_default": False,
                "handles_bw": True,
                "handles_color": True,
                "last_status_message": "Ready"
            }
        )
        PrinterCapability.objects.get_or_create(
            printer=p2,
            defaults={
                "supports_bw": True,
                "supports_color": True,
                "supports_duplex": True,
                "supported_paper_sizes": ["A4", "A3", "LETTER"],
                "dpi": 1200
            }
        )

        # Routing Assignments
        PrinterAssignment.objects.get_or_create(
            shop=shop,
            assignment_type=PrinterAssignment.AssignmentType.BW_SINGLE,
            defaults={"primary_printer": p1}
        )
        PrinterAssignment.objects.get_or_create(
            shop=shop,
            assignment_type=PrinterAssignment.AssignmentType.COLOR_SINGLE,
            defaults={"primary_printer": p2}
        )

        # 6. Sample Live Order
        doc = PrintDocument.objects.create(
            shop=shop,
            original_filename="Project_Report_Final.pdf",
            file_hash_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            encrypted_file=SimpleUploadedFile("report.enc", b"encrypted_sample_data_stream"),
            encrypted_file_size=1024,
            encrypted_key_bundle="sample_wrapped_key_bundle_b64",
            encryption_iv="sample_iv_b64",
            detected_page_count=6,
            verified_page_count=6
        )
        pref = PrintPreference.objects.create(
            color_mode="BW",
            duplex_mode="DOUBLE",
            paper_size="A4",
            copies=1,
            total_calculated_pages=6
        )
        order, o_created = PrintOrder.objects.get_or_create(
            idempotency_key="seed_demo_order_001",
            defaults={
                "order_number": "ORD-20261111-9284",
                "shop": shop,
                "customer_name": "Pooja Sharma",
                "customer_phone": "+91 9898989898",
                "document": doc,
                "preference": pref,
                "status": PrintOrder.Status.PRINTING,
                "total_amount": Decimal("10.50"),
                "pricing_breakdown": {
                    "unit_rate": 3.5,
                    "rate_label": "B&W Double-Sided",
                    "sheets_per_copy": 3,
                    "copies": 1,
                    "total_sheets": 3,
                    "total_amount": 10.50
                }
            }
        )
        if o_created:
            job = PrintJob.objects.create(
                order=order,
                printer=p1,
                status=PrintJob.Status.SUBMITTED_TO_SPOOLER,
                assigned_at=timezone.now(),
                dispatched_at=timezone.now()
            )
            PrintJobAttempt.objects.create(
                job=job,
                printer=p1,
                attempt_number=1,
                status="SUBMITTED_TO_SPOOLER",
                error_message="Submitted to Windows Spooler Queue HP_LaserJet_Pro_M428fdw"
            )

            Payment.objects.create(
                order=order,
                gateway_order_id="order_demo_seed_001",
                gateway_payment_id="pay_demo_seed_001",
                gateway_signature="sig_demo_seed_001",
                gateway_name="RAZORPAY_SANDBOX",
                amount=Decimal("10.50"),
                currency="INR",
                status=Payment.Status.CAPTURED,
                idempotency_key="pay_idemp_seed_001",
                verified_at=timezone.now()
            )

        self.stdout.write(self.style.SUCCESS("KEP PrintGrid seeded with active demo shop, staff, copiers, and orders!"))
