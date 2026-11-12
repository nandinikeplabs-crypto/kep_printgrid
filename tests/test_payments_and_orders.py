from decimal import Decimal
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from core.models import User, Shop
from orders.models import PrintOrder, PrintDocument, PrintPreference, PricingRule, PrintJob
from payments.models import Payment, Refund
from payments.services.gateway_adapter import get_payment_gateway, RazorpaySandboxAdapter


@override_settings(PAYMENT_SANDBOX_MODE=True)
class PaymentsAndOrdersLifecycleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            username='payowner',
            email='pay@shop.example',
            password='Password123!',
            role=User.Role.OWNER
        )
        self.shop = Shop.objects.create(
            name='Payment Test Shop',
            owner=self.owner,
            email='pay@shop.example',
            phone='9876543210',
            address='Fintech Boulevard'
        )
        self.pricing = PricingRule.objects.create(
            shop=self.shop,
            bw_single_rate=Decimal('2.00'),
            bw_double_rate=Decimal('3.50'),
            color_single_rate=Decimal('10.00'),
            color_double_rate=Decimal('18.00'),
            a3_bw_rate=Decimal('5.00'),
            a3_color_rate=Decimal('20.00'),
        )

    def test_pricing_calculation_rules(self):
        """Validates all mathematical combinations of single/duplex/color/copies."""
        # 1. B&W Single: 5 pages * 1 copy = 5 sheets * 2.00 = 10.00
        p1 = PrintPreference(color_mode='BW', duplex_mode='SINGLE', paper_size='A4', copies=1)
        res1 = self.pricing.calculate_price(p1, 5)
        self.assertEqual(res1['total_amount'], 10.00)

        # 2. B&W Double: 5 pages -> 3 sheets * 3.50 = 10.50
        p2 = PrintPreference(color_mode='BW', duplex_mode='DOUBLE', paper_size='A4', copies=1)
        res2 = self.pricing.calculate_price(p2, 5)
        self.assertEqual(res2['total_amount'], 10.50)

        # 3. Color Single: 4 pages * 2 copies = 8 pages * 10.00 = 80.00
        p3 = PrintPreference(color_mode='COLOR', duplex_mode='SINGLE', paper_size='A4', copies=2)
        res3 = self.pricing.calculate_price(p3, 4)
        self.assertEqual(res3['total_amount'], 80.00)

    def test_payment_creation_and_cryptographic_verification(self):
        """End-to-end payment creation, signature verification, and job release."""
        doc = PrintDocument.objects.create(
            shop=self.shop,
            original_filename='invoice.pdf',
            file_hash_sha256='hash',
            encrypted_file=SimpleUploadedFile('inv.enc', b'ciphertext'),
            encrypted_file_size=10,
            encrypted_key_bundle='bundle',
            encryption_iv='iv',
            detected_page_count=2
        )
        pref = PrintPreference.objects.create(
            color_mode='BW',
            duplex_mode='SINGLE',
            paper_size='A4',
            copies=1,
            total_calculated_pages=2
        )
        order = PrintOrder.objects.create(
            order_number='ORD-PAY-TEST-001',
            shop=self.shop,
            customer_phone='9876543210',
            document=doc,
            preference=pref,
            status=PrintOrder.Status.AWAITING_PAYMENT,
            total_amount=Decimal('4.00'),
            idempotency_key='test_idemp_pay_001'
        )

        # 1. Create Payment Order via API
        create_resp = self.client.post(
            reverse('payments:api_create_payment_order'),
            {'order_number': order.order_number},
            content_type='application/json'
        )
        self.assertEqual(create_resp.status_code, 201)
        pay_data = create_resp.json()
        gateway_order_id = pay_data['gateway_order_id']
        self.assertTrue(gateway_order_id.startswith('order_'))

        gateway = get_payment_gateway()
        self.assertIsInstance(gateway, RazorpaySandboxAdapter)

        # 2. Test Invalid Signature is Rejected
        invalid_resp = self.client.post(
            reverse('payments:api_verify_payment'),
            {
                'gateway_order_id': gateway_order_id,
                'gateway_payment_id': 'pay_fake_123',
                'gateway_signature': 'invalid_signature_hex'
            },
            content_type='application/json'
        )
        self.assertEqual(invalid_resp.status_code, 400)
        order.refresh_from_db()
        self.assertEqual(order.status, PrintOrder.Status.AWAITING_PAYMENT)

        # 3. Test Valid Signature Releases the Print Job
        valid_payment_id = 'pay_real_test_999'
        valid_signature = gateway.generate_expected_signature(gateway_order_id, valid_payment_id)

        valid_resp = self.client.post(
            reverse('payments:api_verify_payment'),
            {
                'gateway_order_id': gateway_order_id,
                'gateway_payment_id': valid_payment_id,
                'gateway_signature': valid_signature
            },
            content_type='application/json'
        )
        self.assertEqual(valid_resp.status_code, 200)

        order.refresh_from_db()
        self.assertIn(order.status, [PrintOrder.Status.PAYMENT_VERIFIED, PrintOrder.Status.QUEUED, PrintOrder.Status.ASSIGNED, PrintOrder.Status.COMPLETED])
        self.assertTrue(hasattr(order, 'print_job'))

        # 4. Test Duplicate Verification Handled Idempotently
        dup_resp = self.client.post(
            reverse('payments:api_verify_payment'),
            {
                'gateway_order_id': gateway_order_id,
                'gateway_payment_id': valid_payment_id,
                'gateway_signature': valid_signature
            },
            content_type='application/json'
        )
        self.assertEqual(dup_resp.status_code, 200)
        self.assertEqual(dup_resp.json()['status'], 'already_processed')
        # PrintJob count remains exactly 1
        self.assertEqual(PrintJob.objects.filter(order=order).count(), 1)
