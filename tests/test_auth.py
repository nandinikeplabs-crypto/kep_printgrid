from django.test import TestCase, Client
from django.urls import reverse
from core.models import User, Shop
from orders.models import PricingRule


class AuthenticationAndRegistrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('core:register')
        self.login_url = reverse('core:login')
        self.logout_url = reverse('core:logout')
        self.dashboard_url = reverse('core:owner_overview')

    def test_valid_shop_registration(self):
        """Test complete valid shop owner registration creates user, shop, and pricing."""
        payload = {
            'shop_name': 'Express Print Hub',
            'owner_name': 'Rohit Sharma',
            'email': 'rohit@expressprint.example',
            'mobile_number': '+91 9876543210',
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!',
            'shop_address': 'Shop 10, Metro Station Complex',
        }
        response = self.client.post(self.register_url, payload, follow=True)
        self.assertEqual(response.status_code, 200)

        # Check User creation
        user = User.objects.filter(email='rohit@expressprint.example').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.role, User.Role.OWNER)

        # Check Shop creation
        shop = Shop.objects.filter(owner=user).first()
        self.assertIsNotNone(shop)
        self.assertEqual(shop.name, 'Express Print Hub')
        self.assertTrue(shop.slug.startswith('express-print-hub'))
        self.assertTrue(len(shop.connector_auth_token) > 20)

        # Check default pricing rule
        pricing = PricingRule.objects.filter(shop=shop).first()
        self.assertIsNotNone(pricing)
        self.assertEqual(pricing.bw_single_rate, 2.00)

    def test_duplicate_email_registration_rejected(self):
        """Test registration with an existing email is rejected."""
        User.objects.create_user(
            username='existinguser',
            email='test@shop.example',
            password='Password123!'
        )
        payload = {
            'shop_name': 'Second Shop',
            'owner_name': 'Ajay Dev',
            'email': 'test@shop.example',
            'mobile_number': '+91 9999999999',
            'password': 'Password1234!',
            'confirm_password': 'Password1234!',
            'shop_address': 'Sector 4',
        }
        response = self.client.post(self.register_url, payload)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIn('email', form.errors)
        self.assertIn('An account with this email address already exists. Please log in.', form.errors['email'])

    def test_invalid_password_mismatch(self):
        """Test passwords that do not match are rejected."""
        payload = {
            'shop_name': 'Fail Shop',
            'owner_name': 'Tester',
            'email': 'fail@shop.example',
            'mobile_number': '+91 9111111111',
            'password': 'Password123!',
            'confirm_password': 'DifferentPassword123!',
            'shop_address': 'Main Street',
        }
        response = self.client.post(self.register_url, payload)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIn('confirm_password', form.errors)
        self.assertIn('Passwords do not match.', form.errors['confirm_password'])

    def test_login_and_logout_flow(self):
        """Test authentication via username or email and subsequent session logout."""
        user = User.objects.create_user(
            username='printowner',
            email='owner@test.example',
            password='SuperSecretPassword!',
            role=User.Role.OWNER
        )
        Shop.objects.create(name='Test Shop', owner=user, email=user.email, phone='1234567890', address='Local')

        # Login with email
        login_resp = self.client.post(self.login_url, {
            'email_or_username': 'owner@test.example',
            'password': 'SuperSecretPassword!'
        }, follow=True)
        self.assertEqual(login_resp.status_code, 200)
        self.assertTrue(login_resp.context['user'].is_authenticated)

        # Logout
        logout_resp = self.client.get(self.logout_url, follow=True)
        self.assertFalse(logout_resp.context['user'].is_authenticated)

    def test_unauthorized_dashboard_access_redirects(self):
        """Unauthenticated user accessing protected dashboard route is redirected to login."""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(reverse('core:login') in response.url)
