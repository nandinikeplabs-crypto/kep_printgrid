import uuid
import secrets
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify


class User(AbstractUser):
    class Role(models.TextChoices):
        OWNER = 'OWNER', 'Shop Owner / Admin'
        STAFF = 'STAFF', 'Shop Staff'
        CUSTOMER = 'CUSTOMER', 'Customer'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def is_owner(self):
        return self.role == self.Role.OWNER

    def is_staff_member(self):
        return self.role == self.Role.STAFF

    def is_customer(self):
        return self.role == self.Role.CUSTOMER


class Shop(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_shops')
    slug = models.SlugField(max_length=180, unique=True, db_index=True)
    phone = models.CharField(max_length=25)
    email = models.EmailField()
    address = models.TextField()

    # Operations status
    is_accepting_orders = models.BooleanField(default=True)
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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.slug})"

    def save(self, *args, **kwargs):
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
        base_url = getattr(settings, 'BASE_APP_URL', 'http://127.0.0.1:8000').rstrip('/')
        return f"{base_url}/shop/{self.slug}/"


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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"QR for {self.shop.name}"


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
