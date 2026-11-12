import uuid
from decimal import Decimal
import io
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from core.models import Shop, ShopQRCode
from printers.models import Printer, PrinterCapability
from printers.services.routing_service import RoutingService
from printers.services.test_print_service import generate_printer_test_page
from orders.models import PrintOrder, PrintDocument, PrintPreference, PrintJob, PricingRule

User = get_user_model()


class QRPrinterMappingEndToEndTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Shop A (Kep Xerox)
        self.owner_a = User.objects.create_user(
            username='owner_a',
            email='owner_a@example.com',
            password='Password123!',
            role=User.Role.OWNER
        )
        self.shop_a = Shop.objects.create(
            name='Kep Xerox',
            owner=self.owner_a,
            email='kep@example.com',
            phone='9121604457',
            address='Counter 1, Central Campus'
        )
        PricingRule.objects.create(shop=self.shop_a)
        self.qr_a, _ = ShopQRCode.objects.get_or_create(shop=self.shop_a)

        # Printer A (HP Smart Tank 530)
        self.printer_a = Printer.objects.create(
            shop=self.shop_a,
            name='HP Smart Tank 530',
            system_printer_name='HP_Smart_Tank_530_series',
            is_active=True,
            is_online=True,
            is_default=True,
            handles_bw=True,
            handles_color=True
        )
        PrinterCapability.objects.create(
            printer=self.printer_a,
            supports_bw=True,
            supports_color=True,
            supports_duplex=False,
            supported_paper_sizes=['A4']
        )

        # Shop B (Metro Print)
        self.owner_b = User.objects.create_user(
            username='owner_b',
            email='owner_b@example.com',
            password='Password123!',
            role=User.Role.OWNER
        )
        self.shop_b = Shop.objects.create(
            name='Metro Print',
            owner=self.owner_b,
            email='metro@example.com',
            phone='9876543210',
            address='North Gate Kiosk'
        )
        PricingRule.objects.create(shop=self.shop_b)
        self.qr_b, _ = ShopQRCode.objects.get_or_create(shop=self.shop_b)

        # Printer B (Canon ImageRunner)
        self.printer_b = Printer.objects.create(
            shop=self.shop_b,
            name='Canon ImageRunner',
            system_printer_name='Canon_iR2520_UFRII',
            is_active=True,
            is_online=True,
            is_default=True,
            handles_bw=True,
            handles_color=False
        )
        PrinterCapability.objects.create(
            printer=self.printer_b,
            supports_bw=True,
            supports_color=False,
            supports_duplex=True,
            supported_paper_sizes=['A4', 'A3']
        )

    def test_printer_code_generation(self):
        """Newly created printers automatically receive a unique PRN-XXXXXXXX code."""
        self.assertTrue(self.printer_a.printer_code.startswith('PRN-'))
        self.assertTrue(self.printer_b.printer_code.startswith('PRN-'))
        self.assertNotEqual(self.printer_a.printer_code, self.printer_b.printer_code)

    def test_assign_printer_to_qr_code(self):
        """Shopkeeper assigns a physical printer to their shop's QR code."""
        self.qr_a.assigned_printer = self.printer_a
        self.qr_a.save()
        self.qr_a.refresh_from_db()
        self.assertEqual(self.qr_a.assigned_printer, self.printer_a)
        self.assertEqual(self.qr_a.assigned_printer.system_printer_name, 'HP_Smart_Tank_530_series')

    def _create_test_document(self, shop):
        return PrintDocument.objects.create(
            shop=shop,
            original_filename='test_doc.pdf',
            file_hash_sha256='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
            encrypted_file=SimpleUploadedFile('test.pdf.enc', b'test-encrypted-content'),
            encrypted_file_size=22,
            encrypted_key_bundle='mock-key-bundle',
            encryption_iv='mock-iv',
            encryption_tag='mock-tag',
            detected_page_count=1
        )

    def test_multi_shop_routing_isolation(self):
        """
        Orders placed at Shop A must route strictly to Shop A's assigned printer.
        Orders placed at Shop B must route strictly to Shop B's assigned printer.
        Never cross-route!
        """
        # Assign printers to respective QR codes
        self.qr_a.assigned_printer = self.printer_a
        self.qr_a.save()

        self.qr_b.assigned_printer = self.printer_b
        self.qr_b.save()

        # Create Order for Shop A
        doc_a = self._create_test_document(self.shop_a)
        pref_a = PrintPreference.objects.create(
            color_mode='BW',
            duplex_mode='SINGLE',
            paper_size='A4',
            copies=1,
            total_calculated_pages=1
        )
        order_a = PrintOrder.objects.create(
            shop=self.shop_a,
            document=doc_a,
            qr_code=self.qr_a,
            preference=pref_a,
            status=PrintOrder.Status.PAYMENT_VERIFIED,
            total_amount=Decimal('2.00'),
            idempotency_key=str(uuid.uuid4())
        )

        job_a = RoutingService.route_paid_order(order_a)
        self.assertEqual(job_a.printer, self.printer_a)
        self.assertEqual(job_a.printer.shop, self.shop_a)
        self.assertNotEqual(job_a.printer, self.printer_b)

        # Create Order for Shop B
        doc_b = self._create_test_document(self.shop_b)
        pref_b = PrintPreference.objects.create(
            color_mode='BW',
            duplex_mode='SINGLE',
            paper_size='A4',
            copies=1,
            total_calculated_pages=1
        )
        order_b = PrintOrder.objects.create(
            shop=self.shop_b,
            document=doc_b,
            qr_code=self.qr_b,
            preference=pref_b,
            status=PrintOrder.Status.PAYMENT_VERIFIED,
            total_amount=Decimal('2.00'),
            idempotency_key=str(uuid.uuid4())
        )

        job_b = RoutingService.route_paid_order(order_b)
        self.assertEqual(job_b.printer, self.printer_b)
        self.assertEqual(job_b.printer.shop, self.shop_b)
        self.assertNotEqual(job_b.printer, self.printer_a)

    def test_prevent_cross_shop_printer_assignment_leak(self):
        """
        If Shop A's QR code somehow had Printer B (from Shop B) assigned,
        RoutingService MUST NOT route Shop A's document to Shop B's printer.
        """
        # Malicious or accidental cross-shop foreign key
        self.qr_a.assigned_printer = self.printer_b  # printer_b belongs to shop_b!
        self.qr_a.save()

        doc = self._create_test_document(self.shop_a)
        pref = PrintPreference.objects.create(
            color_mode='BW',
            duplex_mode='SINGLE',
            paper_size='A4',
            copies=1,
            total_calculated_pages=1
        )
        order = PrintOrder.objects.create(
            shop=self.shop_a,
            document=doc,
            qr_code=self.qr_a,
            preference=pref,
            status=PrintOrder.Status.PAYMENT_VERIFIED,
            total_amount=Decimal('2.00'),
            idempotency_key=str(uuid.uuid4())
        )

        job = RoutingService.route_paid_order(order)
        # Must fall back to Shop A's default/capable printer, NEVER Printer B
        self.assertEqual(job.printer, self.printer_a)
        self.assertNotEqual(job.printer, self.printer_b)

    def test_physical_test_print_generation(self):
        """Test print generation creates a valid, non-empty PDF page with calibration graphics."""
        import os
        pdf_path = generate_printer_test_page(self.shop_a, self.printer_a)
        self.assertIsInstance(pdf_path, str)
        self.assertTrue(os.path.exists(pdf_path))
        file_size = os.path.getsize(pdf_path)
        self.assertTrue(file_size > 50000, f"Expected PDF > 50KB, got {file_size}")
        with open(pdf_path, 'rb') as f:
            header = f.read(5)
            self.assertEqual(header, b'%PDF-')
        # Clean up temp file
        try:
            os.remove(pdf_path)
        except OSError:
            pass
