import uuid
import secrets
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify


class User(AbstractUser):
    class Role(models.TextChoices):
        KEP_ADMIN = 'KEP_ADMIN', 'KEP Platform Administrator'
        OWNER = 'OWNER', 'Shop / Institution Administrator'
        STAFF = 'STAFF', 'Shop Operator / Staff'
        CUSTOMER = 'CUSTOMER', 'Customer'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def is_kep_admin(self):
        return self.role == self.Role.KEP_ADMIN or self.is_superuser

    def is_owner(self):
        return self.role == self.Role.OWNER or self.role == self.Role.KEP_ADMIN or self.is_superuser

    def is_staff_member(self):
        return self.role == self.Role.STAFF

    def is_customer(self):
        return self.role == self.Role.CUSTOMER


class Shop(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop_code = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
        blank=True,
        help_text="Unique Shop ID, e.g. KEP12345"
    )
    name = models.CharField(max_length=150)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_shops')
    slug = models.SlugField(max_length=180, unique=True, db_index=True)
    phone = models.CharField(max_length=25)
    email = models.EmailField()
    address = models.TextField()

    # Shop vs Educational/Corporate Institution
    is_institution = models.BooleanField(default=False, help_text="Shop or educational/corporate institution")
    institution_type = models.CharField(max_length=50, blank=True, default="Commercial Xerox Shop")

    # Subscription / Plan Tier
    class PlanTier(models.TextChoices):
        TRIAL = 'TRIAL', 'Trial Plan'
        STARTER = 'STARTER', 'Starter Plan'
        PRO = 'PRO', 'Pro Business Plan'
        ENTERPRISE = 'ENTERPRISE', 'Institutional Enterprise'

    plan_tier = models.CharField(max_length=20, choices=PlanTier.choices, default=PlanTier.TRIAL)
    plan_active = models.BooleanField(default=True)

    # Operations & Setup Readiness
    is_accepting_orders = models.BooleanField(default=True)
    is_checkout_enabled = models.BooleanField(
        default=True,
        help_text="The QR is available during setup, but checkout stays disabled until shop is ready."
    )
    test_order_completed = models.BooleanField(default=False, help_text="Confirmed physical test printout")
    setup_step_completed = models.PositiveSmallIntegerField(default=8)
    pause_message = models.CharField(
        max_length=255,
        default="This shop is temporarily paused and not accepting new print orders at the moment."
    )

    # Windows Local Connector authentication & document encryption key
    connector_auth_token = models.CharField(max_length=128, unique=True, blank=True)
    connector_public_key = models.TextField(
        blank=True,
        help_text="RSA Public Key (PEM) uploaded by the local connector for client-side document key wrapping."
    )
    connector_last_seen = models.DateTimeField(null=True, blank=True)

    # Razorpay Payment Gateway Credentials (Optional per-shop integration)
    razorpay_key_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Shop Razorpay Key ID (rzp_live_... or rzp_test_...). If blank, system default/sandbox is used."
    )
    razorpay_key_secret = models.CharField(
        max_length=100,
        blank=True,
        help_text="Shop Razorpay Key Secret."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.slug})"

    def save(self, *args, **kwargs):
        if not self.shop_code:
            import random
            while True:
                candidate = f"KEP{random.randint(10000, 99999)}"
                if not Shop.objects.filter(shop_code=candidate).exists():
                    self.shop_code = candidate
                    break
        if not self.slug:
            base_slug = slugify(self.name) or "shop"
            unique_part = uuid.uuid4().hex[:8]
            self.slug = f"{base_slug}-{unique_part}"
        if not self.connector_auth_token:
            self.connector_auth_token = secrets.token_urlsafe(48)
        super().save(*args, **kwargs)

    @property
    def order_page_url(self):
        from django.conf import settings
        import socket
        import os

        # 1. First priority: Explicit public tunnel URL for Mobile Data (4G / 5G / Jio / Airtel)
        public_url = getattr(settings, 'PUBLIC_URL', None) or os.getenv('PUBLIC_URL', '')
        if public_url and public_url.strip():
            base_url = public_url.strip().rstrip('/')
            ident = self.shop_code or self.slug
            return f"{base_url}/shop/{ident}/"

        # 2. Check if BASE_APP_URL is a public domain or tunnel
        base_url = getattr(settings, 'BASE_APP_URL', '').rstrip('/')
        if base_url and not any(x in base_url for x in ['127.0.0.1', 'localhost', '192.168.', '10.', '172.']):
            ident = self.shop_code or self.slug
            return f"{base_url}/shop/{ident}/"

        # 3. Dynamic local Wi-Fi IP fallback
        local_ip = "127.0.0.1"
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(('8.8.8.8', 80))
                local_ip = s.getsockname()[0]
        except Exception:
            pass

        base_url = f"http://{local_ip}:8080"
        ident = self.shop_code or self.slug
        return f"{base_url}/shop/{ident}/"


class ShopStaff(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='staff_members')
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    can_manage_printers = models.BooleanField(default=False)
    can_authorize_retries = models.BooleanField(default=True)
    can_manage_pricing = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} @ {self.shop.name}"


class ShopQRCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.OneToOneField(Shop, on_delete=models.CASCADE, related_name='qr_code')
    qr_code_image = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    qr_target_url = models.CharField(max_length=500)
    assigned_printer = models.ForeignKey(
        'printers.Printer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_qr_codes',
        help_text="Physical printer directly mapped to this QR code."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        printer_str = f" -> {self.assigned_printer.name}" if self.assigned_printer else " (Unassigned)"
        return f"QR for {self.shop.name}{printer_str}"


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=True, blank=True, related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.action}] {self.resource_type}:{self.resource_id} by {self.user or 'System'}"
