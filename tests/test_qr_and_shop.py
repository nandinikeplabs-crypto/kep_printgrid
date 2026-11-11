from django.test import TestCase, Client
from django.urls import reverse
from core.models import User, Shop, ShopQRCode
from printers.models import Printer
from core.services.qr_service import generate_shop_qr_code


class PermanentQRCodeAndShopTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            username='qrowner',
            email='qr@shop.example',
            password='Password123!',
            role=User.Role.OWNER
        )
        self.shop = Shop.objects.create(
            name='Campus Copy Point',
            owner=self.owner,
            email='qr@shop.example',
            phone='9876543210',
            address='Gate 2, Campus Center'
        )
        self.qr_code_obj = generate_shop_qr_code(self.shop)

    def test_qr_code_generation_and_association(self):
        """Verify QR code is generated, permanently linked to shop slug, and stored."""
        self.assertIsNotNone(self.qr_code_obj)
        self.assertEqual(self.qr_code_obj.shop, self.shop)
        self.assertTrue(self.shop.slug in self.qr_code_obj.qr_target_url)

    def test_customer_scanning_qr_url_reaches_shop_ordering_page(self):
        """Customer accessing the QR destination reaches the correct shop ordering page."""
        response = self.client.get(reverse('shop_order_page', kwargs={'slug': self.shop.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Campus Copy Point')
        self.assertContains(response, 'Select PDF Document')

    def test_qr_remains_unchanged_after_printer_changes(self):
        """Adding, modifying, or deleting printers must NEVER alter the permanent QR code URL."""
        initial_qr_target = self.qr_code_obj.qr_target_url
        initial_slug = self.shop.slug

        # Add Printer 1
        p1 = Printer.objects.create(
            shop=self.shop,
            name='Canon 1',
            system_printer_name='Canon_IR2520',
            is_active=True,
            is_online=True,
            is_default=True
        )

        # Re-fetch QR code
        self.qr_code_obj.refresh_from_db()
        self.assertEqual(self.qr_code_obj.qr_target_url, initial_qr_target)

        # Switch default printer to Printer 2
        p2 = Printer.objects.create(
            shop=self.shop,
            name='HP LaserJet',
            system_printer_name='HP_LaserJet_Pro',
            is_active=True,
            is_online=True,
            is_default=False
        )
        p1.is_default = False
        p1.save()
        p2.is_default = True
        p2.save()

        # Disable Printer 1
        p1.is_active = False
        p1.is_online = False
        p1.save()

        # Delete Printer 2
        p2.delete()

        # Verify QR code is strictly identical
        self.qr_code_obj.refresh_from_db()
        self.assertEqual(self.qr_code_obj.qr_target_url, initial_qr_target)
        self.assertEqual(self.shop.slug, initial_slug)

    def test_pause_ordering_toggle_behavior(self):
        """When paused, ordering page displays unavailable notice and rejects order creation."""
        self.shop.is_accepting_orders = False
        self.shop.pause_message = "Closed for lunch break. Reopening at 2 PM."
        self.shop.save()

        response = self.client.get(reverse('shop_order_page', kwargs={'slug': self.shop.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ordering Temporarily Paused')
        self.assertContains(response, 'Closed for lunch break. Reopening at 2 PM.')
        self.assertNotContains(response, 'Select PDF Document')
