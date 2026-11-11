from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from core.models import User, Shop
from printers.models import Printer, Connector
from orders.models import PrintOrder, PrintDocument, PrintPreference, PrintJob
from connector.crypto_manager import ConnectorCryptoManager
from connector.local_store import LocalExecutionStore


class ConnectorAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            username='connector_owner',
            email='conn@shop.example',
            password='Password123!',
            role=User.Role.OWNER
        )
        self.shop = Shop.objects.create(
            name='Terminal Xerox',
            owner=self.owner,
            email='conn@shop.example',
            phone='9876543210',
            address='Counter 1'
        )
        self.token = self.shop.connector_auth_token
        self.crypto = ConnectorCryptoManager()

    def test_connector_registration(self):
        """Connector registers machine ID and RSA public key."""
        payload = {
            'machine_id': 'WIN-PC-COUNTER-1',
            'name': 'Windows Desk PC',
            'os_platform': 'win32',
            'version': '1.0.0',
            'rsa_public_key': self.crypto.get_public_key_pem()
        }
        resp = self.client.post(
            reverse('printers:api_connector_register'),
            payload,
            content_type='application/json',
            HTTP_X_SHOP_TOKEN=self.token
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'registered')

        self.shop.refresh_from_db()
        self.assertTrue(self.shop.connector_public_key.startswith('-----BEGIN PUBLIC KEY-----'))
        self.assertEqual(Connector.objects.filter(shop=self.shop).count(), 1)

    def test_connector_heartbeat_syncs_printers(self):
        """Heartbeat auto-discovers and updates shop copiers in cloud DB."""
        payload = {
            'machine_id': 'WIN-PC-COUNTER-1',
            'printers': [
                {
                    'system_name': 'Canon_iR2520_Spooler',
                    'friendly_name': 'Canon imageRUNNER 2520',
                    'is_online': True,
                    'status': 'Ready',
                    'capabilities': {
                        'supports_bw': True,
                        'supports_color': False,
                        'supports_duplex': True,
                        'supported_paper_sizes': ['A4', 'A3']
                    }
                }
            ]
        }
        resp = self.client.post(
            reverse('printers:api_connector_heartbeat'),
            payload,
            content_type='application/json',
            HTTP_X_SHOP_TOKEN=self.token
        )
        self.assertEqual(resp.status_code, 200)

        # Check printer was saved in DB
        printer = Printer.objects.filter(shop=self.shop, system_printer_name='Canon_iR2520_Spooler').first()
        self.assertIsNotNone(printer)
        self.assertTrue(printer.is_online)
        self.assertTrue(printer.capability.supports_duplex)
        self.assertIn('A3', printer.capability.supported_paper_sizes)

    def test_connector_poll_and_status_update_flow(self):
        """Connector polls dispatched jobs and updates status to PHYSICALLY_PRINTED."""
        printer = Printer.objects.create(
            shop=self.shop,
            name='HP LaserJet',
            system_printer_name='HP_LaserJet',
            is_active=True,
            is_online=True
        )
        doc = PrintDocument.objects.create(
            shop=self.shop,
            original_filename='notes.pdf',
            file_hash_sha256='hash',
            encrypted_file=SimpleUploadedFile('notes.enc', b'bytes'),
            encrypted_file_size=5,
            encrypted_key_bundle='bundle',
            encryption_iv='iv',
            detected_page_count=1
        )
        pref = PrintPreference.objects.create(
            color_mode='BW',
            duplex_mode='SINGLE',
            paper_size='A4',
            copies=1,
            total_calculated_pages=1
        )
        order = PrintOrder.objects.create(
            order_number='ORD-CONN-01',
            shop=self.shop,
            customer_phone='9876543210',
            document=doc,
            preference=pref,
            status=PrintOrder.Status.ASSIGNED,
            total_amount=Decimal('2.00'),
            idempotency_key='conn_test_01'
        )
        job = PrintJob.objects.create(
            order=order,
            printer=printer,
            status=PrintJob.Status.DISPATCHED
        )

        # 1. Poll Jobs
        poll_resp = self.client.get(
            reverse('printers:api_connector_poll_jobs'),
            HTTP_X_SHOP_TOKEN=self.token
        )
        self.assertEqual(poll_resp.status_code, 200)
        jobs = poll_resp.json()['pending_jobs']
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]['job_id'], str(job.id))

        # 2. Update Status to PHYSICALLY_PRINTED
        update_resp = self.client.post(
            reverse('printers:api_connector_update_job_status'),
            {
                'job_id': str(job.id),
                'status': PrintJob.Status.PHYSICALLY_PRINTED,
                'verified_page_count': 1,
                'connector_ack_id': 'OS_SPOOL_99'
            },
            content_type='application/json',
            HTTP_X_SHOP_TOKEN=self.token
        )
        self.assertEqual(update_resp.status_code, 200)

        job.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(job.status, PrintJob.Status.PHYSICALLY_PRINTED)
        self.assertEqual(order.status, PrintOrder.Status.COMPLETED)
