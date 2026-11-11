from django.contrib import admin
from .models import Printer, PrinterCapability, PrinterAssignment, Connector, ConnectorHeartbeat


class PrinterCapabilityInline(admin.StackedInline):
    model = PrinterCapability
    can_delete = False


@admin.register(Printer)
class PrinterAdmin(admin.ModelAdmin):
    list_display = ('name', 'system_printer_name', 'shop', 'is_active', 'is_online', 'is_default', 'handles_bw', 'handles_color')
    list_filter = ('is_active', 'is_online', 'is_default', 'handles_bw', 'handles_color', 'shop')
    search_fields = ('name', 'system_printer_name')
    inlines = [PrinterCapabilityInline]


@admin.register(PrinterAssignment)
class PrinterAssignmentAdmin(admin.ModelAdmin):
    list_display = ('shop', 'assignment_type', 'primary_printer', 'fallback_printer', 'updated_at')
    list_filter = ('shop', 'assignment_type')


@admin.register(Connector)
class ConnectorAdmin(admin.ModelAdmin):
    list_display = ('name', 'shop', 'machine_id', 'os_platform', 'is_active', 'last_heartbeat')
    list_filter = ('is_active', 'os_platform', 'shop')


@admin.register(ConnectorHeartbeat)
class ConnectorHeartbeatAdmin(admin.ModelAdmin):
    list_display = ('connector', 'timestamp')
    list_filter = ('connector',)
