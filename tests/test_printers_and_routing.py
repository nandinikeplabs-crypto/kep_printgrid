from decimal import Decimal
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import User, Shop
from printers.models import Printer, PrinterCapability, PrinterAssignment
from orders.models import PrintOrder, PrintDocument, PrintPreference, PrintJob, PricingRule
from printers.services.routing_service import RoutingService


class PrintersAndIntelligentRoutingTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='routingowner',
            email='routing@shop.example',
            password='Password123!',
            role=User.Role.OWNER
        )
        self.shop = Shop.objects.create(
            name='HighTech Xerox',
            owner=self.owner,
            email='routing@shop.example',
            phone='9876543210',
            address='Main Market'
        )
        PricingRule.objects.create(shop=self.shop)

        # Create Printer A: Monochrome High-Speed (B&W only, Single/Duplex, A4)
        self.printer_a = Printer.objects.create(
            shop=self.shop,
            name='Printer A (B&W Fast)',
            system_printer_name='HP_LaserJet_Mono',
            is_active=True,
            is_online=True,
            is_default=True,
            handles_bw=True,
            handles_color=False
        )
        PrinterCapability.objects.create(
            printer=self.printer_a,
            supports_bw=True,
            supports_color=False,
            supports_duplex=True,
            supported_paper_sizes=['A4']
        )

        # Create Printer B: Color Production (B&W + Color, Single/Duplex, A4 + A3)
        self.printer_b = Printer.objects.create(
            shop=self.shop,
            name='Printer B (Canon Color Pro)',
            system_printer_name='Canon_Color_C3530',
            is_active=True,
            is_online=True,
            is_default=False,
            handles_bw=True,
            handles_color=True
        )
        PrinterCapability.objects.create(
            printer=self.printer_b,
            supports_bw=True,
            supports_color=True,
            supports_duplex=True,
            supported_paper_sizes=['A4', 'A3']
        )

    def _create_order(self, color_mode='BW', duplex_mode='SINGLE', paper_size='A4', copies=1):
        doc = PrintDocument.objects.create(
            shop=self.shop,
            original_filename='file.pdf',
            file_hash_sha256='hash123',
            encrypted_file=SimpleUploadedFile('file.pdf.enc', b'encrypted'),
            encrypted_file_size=9,
            encrypted_key_bundle='keybundle',
            encryption_iv='iv',
            detected_page_count=5
        )
        pref = PrintPreference.objects.create(
            color_mode=color_mode,
            duplex_mode=duplex_mode,
            paper_size=paper_size,
            copies=copies,
            total_calculated_pages=5
        )
        order = PrintOrder.objects.create(
            order_number=f"ORD-TEST-{color_mode}-{paper_size}",
            shop=self.shop,
            customer_phone='9876543210',
            document=doc,
            preference=pref,
            status=PrintOrder.Status.PAYMENT_VERIFIED,
            total_amount=Decimal('10.00'),
            idempotency_key=f"idemp_{color_mode}_{paper_size}_{copies}"
        )
        return order

    def test_routing_bw_job_to_printer_a(self):
        """B&W standard job is routed to Printer A (default capable B&W)."""
        order = self._create_order(color_mode='BW', duplex_mode='SINGLE', paper_size='A4')
        job = RoutingService.route_paid_order(order)
        self.assertEqual(job.status, PrintJob.Status.DISPATCHED)
        self.assertEqual(job.printer, self.printer_a)
        self.assertEqual(order.status, PrintOrder.Status.ASSIGNED)

    def test_routing_color_job_to_printer_b(self):
        """Color job must NEVER go to Printer A (monochrome); must route to Printer B."""
        order = self._create_order(color_mode='COLOR', duplex_mode='SINGLE', paper_size='A4')
        job = RoutingService.route_paid_order(order)
        self.assertEqual(job.status, PrintJob.Status.DISPATCHED)
        self.assertEqual(job.printer, self.printer_b)

    def test_routing_a3_job_to_printer_b(self):
        """A3 job must route only to a printer supporting A3 paper size (Printer B)."""
        order = self._create_order(color_mode='BW', duplex_mode='SINGLE', paper_size='A3')
        job = RoutingService.route_paid_order(order)
        self.assertEqual(job.status, PrintJob.Status.DISPATCHED)
        self.assertEqual(job.printer, self.printer_b)

    def test_offline_printer_routes_to_queued_without_failure(self):
        """When required printer is offline and no fallback is eligible, job enters QUEUED state."""
        self.printer_b.is_online = False
        self.printer_b.save()

        # Place Color order (Printer A cannot print color)
        order = self._create_order(color_mode='COLOR', duplex_mode='SINGLE', paper_size='A4')
        job = RoutingService.route_paid_order(order)

        self.assertEqual(job.status, PrintJob.Status.QUEUED)
        self.assertIsNone(job.printer)
        self.assertEqual(order.status, PrintOrder.Status.QUEUED)

    def test_prevent_duplicate_job_creation(self):
        """Calling route_paid_order multiple times on the same order must NEVER duplicate the job."""
        order = self._create_order(color_mode='BW')
        job1 = RoutingService.route_paid_order(order)
        job2 = RoutingService.route_paid_order(order)

        self.assertEqual(job1.id, job2.id)
        self.assertEqual(PrintJob.objects.filter(order=order).count(), 1)

    def test_reassign_incompatible_printer_rejected(self):
        """Attempting to reassign a color job to a monochrome-only printer raises ValueError."""
        order = self._create_order(color_mode='COLOR')
        job = RoutingService.route_paid_order(order)
        job.status = PrintJob.Status.QUEUED
        job.save()

        with self.assertRaises(ValueError):
            RoutingService.reassign_job(job, self.printer_a)
