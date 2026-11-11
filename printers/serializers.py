from rest_framework import serializers
from .models import Printer, PrinterCapability, PrinterAssignment, Connector
from orders.models import PrintJob, PrintOrder


class PrinterCapabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrinterCapability
        fields = ['supports_bw', 'supports_color', 'supports_duplex', 'supported_paper_sizes', 'supports_landscape', 'dpi']


class PrinterSerializer(serializers.ModelSerializer):
    capability = PrinterCapabilitySerializer(read_only=True)

    class Meta:
        model = Printer
        fields = [
            'id', 'name', 'system_printer_name', 'model_name',
            'is_active', 'is_online', 'is_default', 'handles_bw',
            'handles_color', 'last_status_message', 'capability'
        ]


class ConnectorRegisterSerializer(serializers.Serializer):
    machine_id = serializers.CharField(max_length=150)
    name = serializers.CharField(max_length=150)
    os_platform = serializers.CharField(max_length=100, default='Windows')
    version = serializers.CharField(max_length=50, default='1.0.0')
    rsa_public_key = serializers.CharField(required=False, allow_blank=True)


class ConnectorHeartbeatSerializer(serializers.Serializer):
    printers = serializers.ListField(child=serializers.DictField())
    system_metrics = serializers.DictField(required=False, default=dict)


class JobStatusUpdateSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=PrintJob.Status.choices)
    verified_page_count = serializers.IntegerField(required=False, allow_null=True)
    failure_reason = serializers.CharField(required=False, allow_blank=True)
    connector_ack_id = serializers.CharField(required=False, allow_blank=True)
