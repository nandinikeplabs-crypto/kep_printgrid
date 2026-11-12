import logging
from django.utils import timezone
from django.db import transaction
from printers.models import Printer, PrinterAssignment, Connector
from orders.models import PrintOrder, PrintJob, PrintJobAttempt
from core.models import AuditLog

logger = logging.getLogger(__name__)


class RoutingService:
    @classmethod
    def get_eligible_printers(cls, shop, preference, require_online=True):
        """
        Returns a list of printers in the shop that physically and operationally
        satisfy the customer's print preferences.
        """
        qs = Printer.objects.filter(shop=shop, is_active=True)
        if require_online:
            qs = qs.filter(is_online=True)

        eligible = []
        for printer in qs:
            if printer.can_print(
                color_mode=preference.color_mode,
                duplex_mode=preference.duplex_mode,
                paper_size=preference.paper_size
            ):
                eligible.append(printer)
        return eligible

    @classmethod
    def determine_target_printer(cls, shop, preference, qr_code=None):
        """
        Selects the best target printer:
        1. If this order's QR code has an assigned physical printer capable of the job and online, prioritize it.
        2. If the shop's counter QR code has an assigned physical printer capable of the job and online, prioritize it.
        3. Otherwise use PrinterAssignment routing rules (B&W, Color, Duplex, A3).
        4. Otherwise use the shop's default registered printer if capable and online.
        5. Fallback to any online eligible printer belonging to THIS shop.
        6. Return None if no compatible online printer is available, placing the job into QUEUED state.
        NEVER route an order to another shop's printer!
        """
        # 1. Directly check order QR code assigned printer
        if qr_code and qr_code.assigned_printer and qr_code.assigned_printer.shop_id == shop.id:
            assigned = qr_code.assigned_printer
            if assigned.is_active and assigned.is_online and assigned.can_print(preference.color_mode, preference.duplex_mode, preference.paper_size):
                return assigned

        # 2. Check shop's counter QR code assigned printer
        shop_qr = getattr(shop, 'qr_code', None)
        if shop_qr and shop_qr.assigned_printer and shop_qr.assigned_printer.shop_id == shop.id:
            assigned = shop_qr.assigned_printer
            if assigned.is_active and assigned.is_online and assigned.can_print(preference.color_mode, preference.duplex_mode, preference.paper_size):
                return assigned

        # 3. Intelligent Assignment Rules
        is_color = preference.color_mode == 'COLOR'
        is_double = preference.duplex_mode == 'DOUBLE'
        is_a3 = preference.paper_size == 'A3'

        if is_a3:
            assignment_key = PrinterAssignment.AssignmentType.A3_COLOR if is_color else PrinterAssignment.AssignmentType.A3_BW
        else:
            if is_color:
                assignment_key = (
                    PrinterAssignment.AssignmentType.COLOR_DOUBLE if is_double
                    else PrinterAssignment.AssignmentType.COLOR_SINGLE
                )
            else:
                assignment_key = (
                    PrinterAssignment.AssignmentType.BW_DOUBLE if is_double
                    else PrinterAssignment.AssignmentType.BW_SINGLE
                )

        assignment = PrinterAssignment.objects.filter(
            shop=shop,
            assignment_type=assignment_key
        ).select_related('primary_printer', 'fallback_printer').first()

        if assignment:
            primary = assignment.primary_printer
            if primary and primary.is_active and primary.shop_id == shop.id:
                if primary.is_online and primary.can_print(preference.color_mode, preference.duplex_mode, preference.paper_size):
                    return primary
            fallback = assignment.fallback_printer
            if fallback and fallback.is_active and fallback.shop_id == shop.id:
                if fallback.is_online and fallback.can_print(preference.color_mode, preference.duplex_mode, preference.paper_size):
                    return fallback

        # 4. Try shop default registered printer
        default_printer = Printer.objects.filter(shop=shop, is_default=True, is_active=True, is_online=True).first()
        if default_printer and default_printer.can_print(preference.color_mode, preference.duplex_mode, preference.paper_size):
            return default_printer

        # 5. Fallback to any online eligible printer registered to this shop
        eligible = cls.get_eligible_printers(shop, preference, require_online=True)
        if eligible:
            return eligible[0]

        return None

    @classmethod
    @transaction.atomic
    def route_paid_order(cls, order: PrintOrder) -> PrintJob:
        """
        Processes a paid order:
        1. Ensures order status is PAYMENT_VERIFIED or QUEUED.
        2. Dispatches or queues exactly one PrintJob.
        3. Prevents duplicate job creation.
        """
        if hasattr(order, 'print_job'):
            job = order.print_job
            # If job already exists and is not FAILED, return it without creating duplicate
            if job.status not in [PrintJob.Status.FAILED]:
                return job
        else:
            job = PrintJob(order=order)

        shop = order.shop
        qr_code = getattr(order, 'qr_code', None) or getattr(shop, 'qr_code', None)
        target_printer = cls.determine_target_printer(shop, order.preference, qr_code=qr_code)

        # Associate active shop connector
        active_connector = Connector.objects.filter(shop=shop, is_active=True).order_by('-last_heartbeat').first()

        job.connector = active_connector

        if target_printer:
            job.printer = target_printer
            job.status = PrintJob.Status.DISPATCHED
            job.assigned_at = timezone.now()
            job.dispatched_at = timezone.now()
            order.status = PrintOrder.Status.ASSIGNED
        else:
            job.printer = None
            job.status = PrintJob.Status.QUEUED
            order.status = PrintOrder.Status.QUEUED

        job.save()
        order.save()

        # Log attempt
        PrintJobAttempt.objects.create(
            job=job,
            printer=target_printer,
            attempt_number=job.attempts.count() + 1,
            status=job.status,
            error_message="Queued - waiting for compatible online printer" if not target_printer else "Dispatched to target printer"
        )

        AuditLog.objects.create(
            shop=shop,
            action='PRINT_JOB_ROUTED',
            resource_type='PrintJob',
            resource_id=str(job.id),
            details={
                'order_number': order.order_number,
                'target_printer': target_printer.name if target_printer else 'QUEUED_UNASSIGNED',
                'status': job.status,
                'color_mode': order.preference.color_mode,
                'paper_size': order.preference.paper_size,
            }
        )

        return job

    @classmethod
    @transaction.atomic
    def reassign_job(cls, job: PrintJob, new_printer: Printer, user=None):
        """
        Reassigns an eligible QUEUED or FAILED job to an active, compatible printer.
        Never reassigns an already DISPATCHED or PRINTING physical job without authorization.
        """
        if job.status in [PrintJob.Status.SUBMITTED_TO_SPOOLER, PrintJob.Status.PHYSICALLY_PRINTED]:
            raise ValueError("Cannot reassign a job that is already submitted to or completed by the physical printer.")

        pref = job.order.preference
        if not new_printer.can_print(pref.color_mode, pref.duplex_mode, pref.paper_size):
            raise ValueError(f"Selected printer '{new_printer.name}' does not support this document's printing preferences.")

        old_printer_name = job.printer.name if job.printer else "None"
        job.printer = new_printer
        job.status = PrintJob.Status.DISPATCHED
        job.assigned_at = timezone.now()
        job.dispatched_at = timezone.now()
        job.save()

        job.order.status = PrintOrder.Status.ASSIGNED
        job.order.save()

        PrintJobAttempt.objects.create(
            job=job,
            printer=new_printer,
            attempt_number=job.attempts.count() + 1,
            status=PrintJob.Status.DISPATCHED,
            error_message=f"Reassigned from {old_printer_name} to {new_printer.name}",
            authorized_by=user
        )

        AuditLog.objects.create(
            shop=job.order.shop,
            user=user,
            action='PRINT_JOB_REASSIGNED',
            resource_type='PrintJob',
            resource_id=str(job.id),
            details={
                'from_printer': old_printer_name,
                'to_printer': new_printer.name,
                'authorized_by': user.username if user else 'System'
            }
        )
        return job
