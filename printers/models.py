import uuid
from django.db import models
from core.models import Shop


class Printer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='printers')
    name = models.CharField(max_length=150, help_text="Friendly display name in PrintGrid")
    system_printer_name = models.CharField(
        max_length=200,
        help_text="Exact Windows printer spooler queue name (e.g., 'HP LaserJet Pro MFP M428fdw')"
    )
    model_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True, help_text="Owner/Staff operational toggle")
    is_online = models.BooleanField(default=False, help_text="Live connection state reported by connector")
    is_default = models.BooleanField(default=False)
    handles_bw = models.BooleanField(default=True)
    handles_color = models.BooleanField(default=False)
    last_status_message = models.CharField(max_length=255, blank=True, default="Ready")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', 'name']
        unique_together = ('shop', 'system_printer_name')

    @property
    def printer_code(self):
        return f"PRN-{str(self.id)[:8].upper()}"

    @property
    def detailed_status(self):
        if not self.is_active:
            return "Disabled"
        if not self.is_online:
            return "Offline"
        msg = (self.last_status_message or "").lower()
        if "busy" in msg or "printing" in msg:
            return "Busy"
        if "error" in msg or "jam" in msg or "out of paper" in msg:
            return "Error"
        return "Connected"

    def __str__(self):
        status = "Online" if self.is_online else "Offline"
        active = "Active" if self.is_active else "Disabled"
        return f"{self.name} [{status}, {active}]"

    def can_print(self, color_mode, duplex_mode, paper_size):
        """
        Validates whether this printer satisfies the specified print preferences.
        """
        if not self.is_active or not self.is_online:
            return False

        if color_mode == 'COLOR' and not self.handles_color:
            return False
        if color_mode == 'BW' and not self.handles_bw:
            return False

        capability = getattr(self, 'capability', None)
        if capability:
            if color_mode == 'COLOR' and not capability.supports_color:
                return False
            if duplex_mode == 'DOUBLE' and not capability.supports_duplex:
                return False
            if paper_size not in capability.supported_paper_sizes:
                return False

        return True


class PrinterCapability(models.Model):
    printer = models.OneToOneField(Printer, on_delete=models.CASCADE, related_name='capability')
    supports_bw = models.BooleanField(default=True)
    supports_color = models.BooleanField(default=False)
    supports_duplex = models.BooleanField(default=False)
    supported_paper_sizes = models.JSONField(
        default=list,
        help_text="Supported paper size codes, e.g. ['A4', 'A3', 'LETTER']"
    )
    supports_landscape = models.BooleanField(default=True)
    dpi = models.IntegerField(default=600)
    max_copies_per_job = models.IntegerField(default=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Capabilities for {self.printer.name}"


class PrinterAssignment(models.Model):
    class AssignmentType(models.TextChoices):
        BW_SINGLE = 'BW_SINGLE', 'B&W Single-Sided'
        BW_DOUBLE = 'BW_DOUBLE', 'B&W Double-Sided'
        COLOR_SINGLE = 'COLOR_SINGLE', 'Color Single-Sided'
        COLOR_DOUBLE = 'COLOR_DOUBLE', 'Color Double-Sided'
        A3_BW = 'A3_BW', 'A3 B&W'
        A3_COLOR = 'A3_COLOR', 'A3 Color'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='printer_assignments')
    assignment_type = models.CharField(max_length=50, choices=AssignmentType.choices)
    primary_printer = models.ForeignKey(
        Printer,
        on_delete=models.CASCADE,
        related_name='assigned_primary_for'
    )
    fallback_printer = models.ForeignKey(
        Printer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_fallback_for'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('shop', 'assignment_type')

    def __str__(self):
        return f"{self.get_assignment_type_display()} -> {self.primary_printer.name}"


class Connector(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='connectors')
    name = models.CharField(max_length=150)
    machine_id = models.CharField(max_length=150)
    os_platform = models.CharField(max_length=100, default='Windows')
    version = models.CharField(max_length=50, default='1.0.0')
    is_active = models.BooleanField(default=True)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.shop.name})"


class ConnectorHeartbeat(models.Model):
    connector = models.ForeignKey(Connector, on_delete=models.CASCADE, related_name='heartbeats')
    timestamp = models.DateTimeField(auto_now_add=True)
    printers_payload = models.JSONField(default=list)
    system_metrics = models.JSONField(default=dict)

    class Meta:
        ordering = ['-timestamp']
