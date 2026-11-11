from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.conf import settings

from core.models import Shop, AuditLog
from .models import Connector, ConnectorHeartbeat, Printer, PrinterCapability
from orders.models import PrintJob, PrintOrder, PrintJobAttempt
from .serializers import (
    ConnectorRegisterSerializer,
    ConnectorHeartbeatSerializer,
    JobStatusUpdateSerializer
)
from printers.services.routing_service import RoutingService


class ConnectorAuthMixin:
    """
    Validates X-Shop-Token header against shop.connector_auth_token.
    """
    def authenticate_connector(self, request):
        token = request.headers.get('X-Shop-Token') or request.data.get('auth_token')
        shop_slug = request.headers.get('X-Shop-Slug') or request.data.get('shop_slug')

        if not token:
            return None, Response(
                {'error': 'Missing X-Shop-Token authentication header.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            if shop_slug:
                shop = Shop.objects.get(slug=shop_slug, connector_auth_token=token)
            else:
                shop = Shop.objects.get(connector_auth_token=token)
            return shop, None
        except Shop.DoesNotExist:
            return None, Response(
                {'error': 'Invalid connector authentication token or shop identifier.'},
                status=status.HTTP_403_FORBIDDEN
            )


class ConnectorRegisterAPIView(APIView, ConnectorAuthMixin):
    permission_classes = [AllowAny]

    def post(self, request):
        shop, error_resp = self.authenticate_connector(request)
        if error_resp:
            return error_resp

        serializer = ConnectorRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        machine_id = data['machine_id']
        rsa_public_key = data.get('rsa_public_key', '').strip()

        now = timezone.now()
        connector, created = Connector.objects.update_or_create(
            shop=shop,
            machine_id=machine_id,
            defaults={
                'name': data['name'],
                'os_platform': data['os_platform'],
                'version': data['version'],
                'is_active': True,
                'last_heartbeat': now,
                'ip_address': request.META.get('REMOTE_ADDR')
            }
        )

        # Store connector RSA public key on shop if provided
        if rsa_public_key:
            shop.connector_public_key = rsa_public_key

        shop.connector_last_seen = now
        shop.save()

        AuditLog.objects.create(
            shop=shop,
            action='CONNECTOR_REGISTERED',
            resource_type='Connector',
            resource_id=str(connector.id),
            ip_address=request.META.get('REMOTE_ADDR'),
            details={'machine_id': machine_id, 'version': data['version'], 'has_rsa_key': bool(rsa_public_key)}
        )

        return Response({
            'status': 'registered',
            'shop_id': str(shop.id),
            'shop_name': shop.name,
            'shop_slug': shop.slug,
            'connector_id': str(connector.id),
            'has_public_key': bool(shop.connector_public_key),
            'message': f"Connected successfully to {shop.name}."
        })


class ConnectorHeartbeatAPIView(APIView, ConnectorAuthMixin):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        shop, error_resp = self.authenticate_connector(request)
        if error_resp:
            return error_resp

        serializer = ConnectorHeartbeatSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        shop.connector_last_seen = now
        shop.save(update_fields=['connector_last_seen'])

        machine_id = request.data.get('machine_id')
        connector = Connector.objects.filter(shop=shop, machine_id=machine_id).first()
        if not connector:
            connector = Connector.objects.filter(shop=shop).order_by('-created_at').first()

        if connector:
            connector.last_heartbeat = now
            connector.save(update_fields=['last_heartbeat'])

            ConnectorHeartbeat.objects.create(
                connector=connector,
                printers_payload=serializer.validated_data.get('printers', []),
                system_metrics=serializer.validated_data.get('system_metrics', {})
            )

        # Auto-discover or synchronize printers reported by local connector
        printers_list = serializer.validated_data.get('printers', [])
        active_printer_names = []

        for p_data in printers_list:
            sys_name = p_data.get('system_name', '').strip()
            friendly_name = p_data.get('friendly_name', sys_name)
            if not sys_name:
                continue

            active_printer_names.append(sys_name)
            is_online = p_data.get('is_online', True)
            status_msg = p_data.get('status', 'Ready')
            caps = p_data.get('capabilities', {})

            printer, created = Printer.objects.get_or_create(
                shop=shop,
                system_printer_name=sys_name,
                defaults={
                    'name': friendly_name,
                    'is_online': is_online,
                    'is_active': True,
                    'last_status_message': status_msg,
                    'handles_bw': caps.get('supports_bw', True),
                    'handles_color': caps.get('supports_color', False),
                }
            )

            if not created:
                printer.is_online = is_online
                printer.last_status_message = status_msg
                printer.handles_bw = caps.get('supports_bw', printer.handles_bw)
                printer.handles_color = caps.get('supports_color', printer.handles_color)
                printer.save()

            # Ensure capability model exists
            PrinterCapability.objects.update_or_create(
                printer=printer,
                defaults={
                    'supports_bw': caps.get('supports_bw', True),
                    'supports_color': caps.get('supports_color', False),
                    'supports_duplex': caps.get('supports_duplex', False),
                    'supported_paper_sizes': caps.get('supported_paper_sizes', ['A4']),
                    'supports_landscape': caps.get('supports_landscape', True),
                    'dpi': caps.get('dpi', 600),
                }
            )

        # Mark printers not seen in heartbeat as offline
        if active_printer_names:
            Printer.objects.filter(shop=shop).exclude(system_printer_name__in=active_printer_names).update(is_online=False)

        # Intelligent routing pass: check if any unassigned QUEUED jobs can now be routed
        unassigned_jobs = PrintJob.objects.filter(
            order__shop=shop,
            status=PrintJob.Status.QUEUED,
            printer__isnull=True
        ).select_related('order', 'order__preference')

        dispatched_count = 0
        for job in unassigned_jobs:
            target = RoutingService.determine_target_printer(shop, job.order.preference)
            if target:
                job.printer = target
                job.status = PrintJob.Status.DISPATCHED
                job.assigned_at = now
                job.dispatched_at = now
                job.save()
                job.order.status = PrintOrder.Status.ASSIGNED
                job.order.save()
                dispatched_count += 1

        return Response({
            'status': 'ok',
            'printers_synced': len(printers_list),
            'dispatched_queued_jobs': dispatched_count
        })


class ConnectorPollJobsAPIView(APIView, ConnectorAuthMixin):
    permission_classes = [AllowAny]

    def get(self, request):
        shop, error_resp = self.authenticate_connector(request)
        if error_resp:
            return error_resp

        # Fetch all dispatched jobs for this shop
        jobs = PrintJob.objects.filter(
            order__shop=shop,
            status=PrintJob.Status.DISPATCHED
        ).select_related('order', 'order__document', 'order__preference', 'printer')

        base_url = getattr(settings, 'BASE_APP_URL', 'http://127.0.0.1:8000').rstrip('/')

        jobs_payload = []
        for job in jobs:
            order = job.order
            doc = order.document
            pref = order.preference

            download_url = f"{base_url}/orders/api/document/{doc.id}/download/?token={shop.connector_auth_token}"

            jobs_payload.append({
                'job_id': str(job.id),
                'order_number': order.order_number,
                'printer_system_name': job.printer.system_printer_name if job.printer else '',
                'printer_friendly_name': job.printer.name if job.printer else '',
                'download_url': download_url,
                'original_filename': doc.original_filename,
                'file_hash_sha256': doc.file_hash_sha256,
                'encrypted_key_bundle': doc.encrypted_key_bundle,
                'encryption_iv': doc.encryption_iv,
                'encryption_tag': doc.encryption_tag,
                'expected_page_count': doc.detected_page_count,
                'preferences': {
                    'color_mode': pref.color_mode,
                    'duplex_mode': pref.duplex_mode,
                    'paper_size': pref.paper_size,
                    'copies': pref.copies,
                    'page_range_type': pref.page_range_type,
                    'page_range_selection': pref.page_range_selection,
                }
            })

        return Response({'pending_jobs': jobs_payload, 'count': len(jobs_payload)})


class ConnectorUpdateJobStatusAPIView(APIView, ConnectorAuthMixin):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        shop, error_resp = self.authenticate_connector(request)
        if error_resp:
            return error_resp

        serializer = JobStatusUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        job = get_object_or_404(PrintJob, id=data['job_id'], order__shop=shop)
        new_status = data['status']
        verified_pages = data.get('verified_page_count')
        failure_reason = data.get('failure_reason', '')
        ack_id = data.get('connector_ack_id', '')

        now = timezone.now()
        job.status = new_status
        if ack_id:
            job.connector_ack_id = ack_id
        if failure_reason:
            job.failure_reason = failure_reason

        # Synchronize order status
        order = job.order
        doc = order.document

        if verified_pages is not None:
            doc.verified_page_count = verified_pages
            doc.save(update_fields=['verified_page_count'])

            # Safety check: if verified pages exceed paid pages, hold verification
            if verified_pages > doc.detected_page_count:
                job.status = PrintJob.Status.HOLD_VERIFICATION
                job.failure_reason = (
                    f"Page count mismatch! Customer paid for {doc.detected_page_count} pages, "
                    f"but decrypted document contains {verified_pages} pages."
                )
                order.status = PrintOrder.Status.FAILED
                job.save()
                order.save()
                return Response({
                    'status': 'held',
                    'action': 'HOLD_VERIFICATION',
                    'message': job.failure_reason
                })

        if new_status == PrintJob.Status.RECEIVED_BY_CONNECTOR:
            order.status = PrintOrder.Status.PRINTING
        elif new_status == PrintJob.Status.SUBMITTED_TO_SPOOLER:
            order.status = PrintOrder.Status.PRINTING
        elif new_status == PrintJob.Status.PHYSICALLY_PRINTED:
            order.status = PrintOrder.Status.COMPLETED
            job.completed_at = now
        elif new_status == PrintJob.Status.FAILED:
            order.status = PrintOrder.Status.FAILED
        elif new_status == PrintJob.Status.HOLD_VERIFICATION:
            order.status = PrintOrder.Status.FAILED

        job.save()
        order.save()

        PrintJobAttempt.objects.create(
            job=job,
            printer=job.printer,
            attempt_number=job.attempts.count() + 1,
            status=new_status,
            error_message=failure_reason
        )

        AuditLog.objects.create(
            shop=shop,
            action='PRINT_JOB_STATUS_UPDATED',
            resource_type='PrintJob',
            resource_id=str(job.id),
            details={
                'order_number': order.order_number,
                'new_status': new_status,
                'verified_page_count': verified_pages,
                'failure_reason': failure_reason
            }
        )

        return Response({
            'status': 'updated',
            'job_id': str(job.id),
            'order_status': order.status,
            'job_status': job.status
        })
