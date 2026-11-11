# KEP PrintGrid - Shop Module Codebase

This document contains all source code related to **Shops, Permanent QR Codes, Printer Management, Pricing, and Shop Operations** in KEP PrintGrid.

---

## 1. Shop & Staff Models (`core/models.py`)

```python
import uuid
import secrets
from django.db import models
from django.utils.text import slugify

class Shop(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    owner = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='owned_shops')
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
        base_url = getattr(settings, 'BASE_APP_URL', 'http://127.0.0.1:8080').rstrip('/')
        return f"{base_url}/shop/{self.slug}/"


class ShopStaff(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='staff_members')
    user = models.OneToOneField('core.User', on_delete=models.CASCADE, related_name='staff_profile')
    can_manage_printers = models.BooleanField(default=False)
    can_authorize_retries = models.BooleanField(default=True)
    can_manage_pricing = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class ShopQRCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.OneToOneField(Shop, on_delete=models.CASCADE, related_name='qr_code')
    qr_code_image = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    qr_target_url = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=True, blank=True, related_name='audit_logs')
    user = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## 2. Permanent QR Code Service (`core/services/qr_service.py`)

```python
import os
import qrcode
from PIL import Image, ImageDraw
from django.conf import settings

def generate_shop_qr_code(shop):
    """
    Generates a permanent QR code PNG and printable A4 PDF poster stand for the shop.
    Changing printers never invalidates this QR code.
    """
    from core.models import ShopQRCode

    target_url = shop.order_page_url

    # 1. Generate QR Code image with Pillow
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=4,
    )
    qr.add_data(target_url)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="#0F172A", back_color="#FFFFFF").convert("RGB")

    # Save PNG
    qr_filename = f"shop_qr_{shop.slug}.png"
    qr_rel_path = f"qr_codes/{qr_filename}"
    full_qr_path = os.path.join(settings.MEDIA_ROOT, qr_rel_path)
    os.makedirs(os.path.dirname(full_qr_path), exist_ok=True)
    qr_img.save(full_qr_path, format="PNG")

    # 2. Generate Printable A4 Poster (1240 x 1754 px @ 150 DPI)
    poster_w, poster_h = 1240, 1754
    poster = Image.new("RGB", (poster_w, poster_h), color="#F8FAFC")
    p_draw = ImageDraw.Draw(poster)

    # Top header banner
    p_draw.rectangle([0, 0, poster_w, 240], fill="#0F172A")
    p_draw.text((poster_w // 2, 70), "KEP PRINTGRID", fill="#38BDF8", anchor="mm")
    p_draw.text((poster_w // 2, 140), "Self-Service Document Printing", fill="#FFFFFF", anchor="mm")
    p_draw.text((poster_w // 2, 190), "Scan • Upload • Pay • Print Instantly", fill="#94A3B8", anchor="mm")

    # Shop Name Card
    p_draw.rounded_rectangle([80, 300, poster_w - 80, 1580], radius=24, fill="#FFFFFF", outline="#E2E8F0", width=3)
    p_draw.text((poster_w // 2, 380), shop.name.upper(), fill="#0F172A", anchor="mm")
    p_draw.text((poster_w // 2, 430), f"Shop Address: {shop.address[:60]}", fill="#64748B", anchor="mm")

    # Paste QR Code
    display_qr_size = 650
    resized_qr = qr_img.resize((display_qr_size, display_qr_size), Image.Resampling.LANCZOS)
    qr_x = (poster_w - display_qr_size) // 2
    poster.paste(resized_qr, (qr_x, 500))

    # Instructions
    p_draw.text((poster_w // 2, 1220), "HOW TO PRINT:", fill="#0F172A", anchor="mm")
    p_draw.text((poster_w // 2, 1280), "1. Scan this permanent QR code using your phone camera", fill="#334155", anchor="mm")
    p_draw.text((poster_w // 2, 1340), "2. Choose your PDF document and printing preferences", fill="#334155", anchor="mm")
    p_draw.text((poster_w // 2, 1400), "3. Pay securely online (UPI / Card / NetBanking)", fill="#334155", anchor="mm")
    p_draw.text((poster_w // 2, 1460), "4. Collect your freshly printed pages at the counter!", fill="#2563EB", anchor="mm")

    pdf_filename = f"shop_qr_{shop.slug}_poster.pdf"
    full_pdf_path = os.path.join(settings.MEDIA_ROOT, "qr_codes", pdf_filename)
    poster.save(full_pdf_path, "PDF", resolution=150.0)

    qrcode_obj, _ = ShopQRCode.objects.update_or_create(
        shop=shop,
        defaults={'qr_code_image': qr_rel_path, 'qr_target_url': target_url}
    )
    return qrcode_obj
```

---

## 3. Shop Operations & Dashboard Views (`core/views.py`)

```python
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Q
from decimal import Decimal
import os
from django.http import FileResponse, Http404

from .models import Shop, AuditLog
from .forms import ShopSettingsForm, StaffCreateForm
from .decorators import owner_required, get_user_shop
from core.services.qr_service import generate_shop_qr_code
from orders.models import PrintOrder
from printers.models import Printer


@owner_required
def owner_overview(request):
    shop = get_user_shop(request.user)
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    shop_orders = PrintOrder.objects.filter(shop=shop)
    total_orders = shop_orders.count()
    today_orders = shop_orders.filter(created_at__gte=today_start).count()
    pending_orders = shop_orders.filter(status__in=[
        PrintOrder.Status.PAYMENT_VERIFIED,
        PrintOrder.Status.QUEUED,
        PrintOrder.Status.ASSIGNED
    ]).count()
    printing_orders = shop_orders.filter(status__in=[
        PrintOrder.Status.SENT_TO_PRINTER,
        PrintOrder.Status.PRINTING
    ]).count()

    today_revenue = shop_orders.filter(
        created_at__gte=today_start,
        status__in=[PrintOrder.Status.PAYMENT_VERIFIED, PrintOrder.Status.COMPLETED]
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')

    shop_printers = Printer.objects.filter(shop=shop)
    online_printers = shop_printers.filter(is_online=True, is_active=True).count()
    offline_printers = shop_printers.filter(Q(is_online=False) | Q(is_active=False)).count()

    return render(request, 'core/owner_overview.html', {
        'shop': shop,
        'total_orders': total_orders,
        'today_orders': today_orders,
        'pending_orders': pending_orders,
        'printing_orders': printing_orders,
        'today_revenue': today_revenue,
        'online_printers': online_printers,
        'offline_printers': offline_printers,
        'shop_printers': shop_printers,
    })


@owner_required
def shop_qr_management(request):
    shop = get_user_shop(request.user)
    qr_record = getattr(shop, 'qr_code', None) or generate_shop_qr_code(shop)
    return render(request, 'core/shop_qr_management.html', {'shop': shop, 'qr_record': qr_record})


@owner_required
def download_qr_asset(request, asset_type):
    shop = get_user_shop(request.user)
    if asset_type == 'png':
        qr_path = os.path.join('media', 'qr_codes', f"shop_qr_{shop.slug}.png")
        return FileResponse(open(qr_path, 'rb'), as_attachment=True, filename=f"{shop.slug}_qr.png")
    elif asset_type == 'pdf':
        pdf_path = os.path.join('media', 'qr_codes', f"shop_qr_{shop.slug}_poster.pdf")
        return FileResponse(open(pdf_path, 'rb'), as_attachment=True, filename=f"{shop.slug}_poster.pdf")
    raise Http404("Asset not found")


@owner_required
def shop_settings(request):
    shop = get_user_shop(request.user)
    if request.method == 'POST':
        form = ShopSettingsForm(request.POST, instance=shop)
        if form.is_valid():
            form.save()
            messages.success(request, "Shop settings saved successfully.")
            return redirect('core:shop_settings')
    else:
        form = ShopSettingsForm(instance=shop)
    return render(request, 'core/shop_settings.html', {'shop': shop, 'form': form})
```

---

## 4. Intelligent Printer Routing for Shops (`printers/services/routing_service.py`)

```python
from django.utils import timezone
from django.db import transaction
from printers.models import Printer, PrinterAssignment
from orders.models import PrintOrder, PrintJob, PrintJobAttempt

class RoutingService:
    @classmethod
    def determine_target_printer(cls, shop, preference):
        """
        Intelligently selects the best available printer matching color, duplex, and paper size.
        """
        is_color = preference.color_mode == 'COLOR'
        is_double = preference.duplex_mode == 'DOUBLE'

        assignment_key = PrinterAssignment.AssignmentType.COLOR_SINGLE if is_color else PrinterAssignment.AssignmentType.BW_SINGLE

        assignment = PrinterAssignment.objects.filter(shop=shop, assignment_type=assignment_key).first()
        if assignment and assignment.primary_printer.is_online and assignment.primary_printer.is_active:
            return assignment.primary_printer

        # Fallback to default printer if capable
        default = Printer.objects.filter(shop=shop, is_default=True, is_active=True, is_online=True).first()
        if default and default.can_print(preference.color_mode, preference.duplex_mode, preference.paper_size):
            return default

        # Any eligible online printer
        for p in Printer.objects.filter(shop=shop, is_active=True, is_online=True):
            if p.can_print(preference.color_mode, preference.duplex_mode, preference.paper_size):
                return p
        return None

    @classmethod
    @transaction.atomic
    def route_paid_order(cls, order: PrintOrder) -> PrintJob:
        if hasattr(order, 'print_job'):
            return order.print_job

        target_printer = cls.determine_target_printer(order.shop, order.preference)
        job = PrintJob(order=order)

        if target_printer:
            job.printer = target_printer
            job.status = PrintJob.Status.DISPATCHED
            job.dispatched_at = timezone.now()
            order.status = PrintOrder.Status.ASSIGNED
        else:
            job.status = PrintJob.Status.QUEUED
            order.status = PrintOrder.Status.QUEUED

        job.save()
        order.save()
        return job
```

---

## 5. Shop Pricing Rules (`orders/models.py`)

```python
from decimal import Decimal
from django.db import models

class PricingRule(models.Model):
    shop = models.ForeignKey('core.Shop', on_delete=models.CASCADE, related_name='pricing_rules')
    bw_single_rate = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('2.00'))
    bw_double_rate = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('3.50'))
    color_single_rate = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('10.00'))
    color_double_rate = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('18.00'))
    a3_bw_rate = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('5.00'))
    a3_color_rate = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('20.00'))
    is_active = models.BooleanField(default=True)

    def calculate_price(self, preference, num_pages: int) -> dict:
        copies = max(1, preference.copies)
        pages = max(1, num_pages)
        color = preference.color_mode
        duplex = preference.duplex_mode

        if color == 'COLOR':
            unit_rate = self.color_double_rate if duplex == 'DOUBLE' else self.color_single_rate
        else:
            unit_rate = self.bw_double_rate if duplex == 'DOUBLE' else self.bw_single_rate

        sheets = (pages + 1) // 2 if duplex == 'DOUBLE' else pages
        total = round(unit_rate * sheets * copies, 2)

        return {
            'unit_rate': float(unit_rate),
            'total_sheets': sheets * copies,
            'total_amount': float(total),
            'currency': 'INR'
        }
```

---

## 6. Shop & Permanent QR Unit Tests (`tests/test_qr_and_shop.py`)

```python
from django.test import TestCase, Client
from django.urls import reverse
from core.models import User, Shop
from printers.models import Printer
from core.services.qr_service import generate_shop_qr_code

class ShopAndQRTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='o1', email='o1@test.com', password='Password123!')
        self.shop = Shop.objects.create(name='Test Xerox', owner=self.owner, phone='9876543210', address='Main Gate')
        self.qr = generate_shop_qr_code(self.shop)

    def test_qr_never_changes_after_printer_switch(self):
        initial_qr = self.qr.qr_target_url
        p1 = Printer.objects.create(shop=self.shop, name='P1', system_printer_name='HP_Laser', is_default=True)
        p2 = Printer.objects.create(shop=self.shop, name='P2', system_printer_name='Canon_IR', is_default=False)
        p1.delete()
        p2.is_default = True
        p2.save()

        self.qr.refresh_from_db()
        self.assertEqual(self.qr.qr_target_url, initial_qr)
```
