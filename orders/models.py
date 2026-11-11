import uuid
from decimal import Decimal
from django.db import models
from core.models import Shop, User
from printers.models import Printer, Connector


class PrintDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='documents')
    original_filename = models.CharField(max_length=255)
    file_hash_sha256 = models.CharField(max_length=64, help_text="Cryptographic hash of encrypted payload")
    encrypted_file = models.FileField(upload_to='encrypted_docs/')
    encrypted_file_size = models.BigIntegerField(default=0)

    # Client-side encryption envelope (Zero-Knowledge)
    # The client generates random AES-256 key, encrypts PDF, and wraps AES key with Shop RSA-OAEP public key.
    encrypted_key_bundle = models.TextField(
        help_text="Base64 encoded AES key wrapped with shop's RSA public key"
    )
    encryption_iv = models.CharField(max_length=64, help_text="Base64 encoded AES-GCM IV (12 bytes)")
    encryption_tag = models.CharField(max_length=64, help_text="Base64 encoded AES-GCM auth tag (16 bytes)")

    detected_page_count = models.PositiveIntegerField(default=1)
    verified_page_count = models.PositiveIntegerField(null=True, blank=True, help_text="Verified locally by connector")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.original_filename} ({self.detected_page_count} pages)"


class PrintPreference(models.Model):
    class ColorMode(models.TextChoices):
        BW = 'BW', 'Black & White'
        COLOR = 'COLOR', 'Color'

    class DuplexMode(models.TextChoices):
        SINGLE = 'SINGLE', 'Single-Sided'
        DOUBLE = 'DOUBLE', 'Double-Sided'

    class PaperSize(models.TextChoices):
        A4 = 'A4', 'A4 (210 x 297 mm)'
        A3 = 'A3', 'A3 (297 x 420 mm)'

    class PageRangeType(models.TextChoices):
        ALL = 'ALL', 'All Pages'
        CUSTOM = 'CUSTOM', 'Custom Range'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    color_mode = models.CharField(max_length=10, choices=ColorMode.choices, default=ColorMode.BW)
    duplex_mode = models.CharField(max_length=10, choices=DuplexMode.choices, default=DuplexMode.SINGLE)
    paper_size = models.CharField(max_length=10, choices=PaperSize.choices, default=PaperSize.A4)
    copies = models.PositiveIntegerField(default=1)
    page_range_type = models.CharField(max_length=10, choices=PageRangeType.choices, default=PageRangeType.ALL)
    page_range_selection = models.CharField(max_length=255, blank=True, default="", help_text="e.g. 1-5, 8, 11-14")
    total_calculated_pages = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.color_mode} | {self.duplex_mode} | {self.paper_size} x {self.copies}"


class PricingRule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='pricing_rules')
    bw_single_rate = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('2.00'))
    bw_double_rate = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('3.50'))
    color_single_rate = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('10.00'))
    color_double_rate = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('18.00'))
    a3_bw_rate = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('5.00'))
    a3_color_rate = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('20.00'))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_price(self, preference: PrintPreference, num_pages: int) -> dict:
        """
        Calculates exact price based on configured rates.
        Returns a dict breakdown and total amount.
        """
        copies = max(1, preference.copies)
        pages_to_print = max(1, num_pages)
        color = preference.color_mode
        duplex = preference.duplex_mode
        paper = preference.paper_size

        if paper == 'A3':
            unit_rate = self.a3_color_rate if color == 'COLOR' else self.a3_bw_rate
            rate_label = f"A3 {color} (per page)"
            sheets = pages_to_print
        else:
            if color == 'COLOR':
                if duplex == 'DOUBLE':
                    # Rate per sheet (2 pages)
                    sheets = (pages_to_print + 1) // 2
                    unit_rate = self.color_double_rate
                    rate_label = "Color Double-Sided (per sheet)"
                else:
                    sheets = pages_to_print
                    unit_rate = self.color_single_rate
                    rate_label = "Color Single-Sided (per page)"
            else:
                if duplex == 'DOUBLE':
                    sheets = (pages_to_print + 1) // 2
                    unit_rate = self.bw_double_rate
                    rate_label = "B&W Double-Sided (per sheet)"
                else:
                    sheets = pages_to_print
                    unit_rate = self.bw_single_rate
                    rate_label = "B&W Single-Sided (per page)"

        subtotal = unit_rate * sheets * copies
        total_amount = round(subtotal, 2)

        return {
            'unit_rate': float(unit_rate),
            'rate_label': rate_label,
            'sheets_per_copy': sheets,
            'pages_per_copy': pages_to_print,
            'copies': copies,
            'total_sheets': sheets * copies,
            'total_amount': float(total_amount),
            'currency': 'INR',
        }


class PrintOrder(models.Model):
    class Status(models.TextChoices):
        UPLOADED = 'UPLOADED', 'Uploaded'
        AWAITING_PAYMENT = 'AWAITING_PAYMENT', 'Awaiting Payment'
        PAYMENT_VERIFIED = 'PAYMENT_VERIFIED', 'Payment Verified'
        QUEUED = 'QUEUED', 'Queued'
        ASSIGNED = 'ASSIGNED', 'Assigned to Printer'
        SENT_TO_PRINTER = 'SENT_TO_PRINTER', 'Sent to Printer'
        PRINTING = 'PRINTING', 'Printing in Progress'
        COMPLETED = 'COMPLETED', 'Completed & Ready for Pickup'
        FAILED = 'FAILED', 'Print Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        REFUND_PENDING = 'REFUND_PENDING', 'Refund Pending'
        REFUNDED = 'REFUNDED', 'Refunded'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=32, unique=True, db_index=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='orders')
    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='customer_orders')
    customer_phone = models.CharField(max_length=20)
    customer_name = models.CharField(max_length=150, default='Walk-in Customer')
    document = models.OneToOneField(PrintDocument, on_delete=models.CASCADE, related_name='order')
    preference = models.OneToOneField(PrintPreference, on_delete=models.CASCADE, related_name='order')
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.UPLOADED, db_index=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    pricing_breakdown = models.JSONField(default=dict)
    idempotency_key = models.CharField(max_length=128, unique=True, db_index=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_number} - {self.get_status_display()} ({self.total_amount} INR)"


class PrintJob(models.Model):
    class Status(models.TextChoices):
        QUEUED = 'QUEUED', 'Queued for Dispatch'
        DISPATCHED = 'DISPATCHED', 'Dispatched to Connector'
        RECEIVED_BY_CONNECTOR = 'RECEIVED_BY_CONNECTOR', 'Received & Decrypted by Connector'
        SUBMITTED_TO_SPOOLER = 'SUBMITTED_TO_SPOOLER', 'Submitted to Windows Spooler'
        PHYSICALLY_PRINTED = 'PHYSICALLY_PRINTED', 'Physically Printed'
        FAILED = 'FAILED', 'Execution Failed'
        HOLD_VERIFICATION = 'HOLD_VERIFICATION', 'Held for Owner Verification (Page mismatch)'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(PrintOrder, on_delete=models.CASCADE, related_name='print_job')
    printer = models.ForeignKey(Printer, on_delete=models.SET_NULL, null=True, blank=True, related_name='print_jobs')
    connector = models.ForeignKey(Connector, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_jobs')
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.QUEUED, db_index=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)
    connector_ack_id = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        printer_name = self.printer.name if self.printer else "Unassigned"
        return f"Job for {self.order.order_number} -> {printer_name} [{self.status}]"


class PrintJobAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(PrintJob, on_delete=models.CASCADE, related_name='attempts')
    printer = models.ForeignKey(Printer, on_delete=models.SET_NULL, null=True, blank=True)
    attempt_number = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=30)
    error_message = models.TextField(blank=True)
    authorized_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
