from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction

from core.decorators import owner_required, get_user_shop
from core.models import AuditLog
from .models import Printer, PrinterCapability, PrinterAssignment
from orders.models import PrintJob
from printers.services.routing_service import RoutingService


@owner_required
def printer_list(request):
    """
    Overview of all printers configured for the shop.
    """
    shop = get_user_shop(request.user)
    printers = Printer.objects.filter(shop=shop).select_related('capability')

    context = {
        'shop': shop,
        'printers': printers,
    }
    return render(request, 'printers/printer_list.html', context)


@owner_required
def printer_toggle_active(request, printer_id):
    """
    Toggles printer active status.
    """
    shop = get_user_shop(request.user)
    printer = get_object_or_404(Printer, id=printer_id, shop=shop)
    printer.is_active = not printer.is_active
    printer.save()

    AuditLog.objects.create(
        shop=shop,
        user=request.user,
        action='PRINTER_STATUS_TOGGLED',
        resource_type='Printer',
        resource_id=str(printer.id),
        details={'printer_name': printer.name, 'is_active': printer.is_active}
    )
    status_str = "enabled" if printer.is_active else "disabled"
    messages.info(request, f"Printer '{printer.name}' has been {status_str}.")
    return redirect('printers:printer_list')


@owner_required
def printer_set_default(request, printer_id):
    """
    Sets the selected printer as shop default printer.
    """
    shop = get_user_shop(request.user)
    with transaction.atomic():
        Printer.objects.filter(shop=shop).update(is_default=False)
        printer = get_object_or_404(Printer, id=printer_id, shop=shop)
        printer.is_default = True
        printer.save()

    AuditLog.objects.create(
        shop=shop,
        user=request.user,
        action='DEFAULT_PRINTER_CHANGED',
        resource_type='Printer',
        resource_id=str(printer.id),
        details={'default_printer': printer.name}
    )
    messages.success(request, f"'{printer.name}' is now the default printer for your shop.")
    return redirect('printers:printer_list')


@owner_required
def printer_assignments_view(request):
    """
    Manages intelligent job routing assignments for B&W, Color, Duplex, and A3 jobs.
    """
    shop = get_user_shop(request.user)
    printers = Printer.objects.filter(shop=shop, is_active=True)
    assignments = PrinterAssignment.objects.filter(shop=shop).select_related('primary_printer', 'fallback_printer')

    assignment_map = {a.assignment_type: a for a in assignments}
    assignment_types = PrinterAssignment.AssignmentType.choices

    if request.method == 'POST':
        with transaction.atomic():
            for code, label in assignment_types:
                primary_id = request.POST.get(f'primary_{code}')
                fallback_id = request.POST.get(f'fallback_{code}')

                if primary_id:
                    primary_p = printers.filter(id=primary_id).first()
                    fallback_p = printers.filter(id=fallback_id).first() if fallback_id else None

                    if primary_p:
                        PrinterAssignment.objects.update_or_create(
                            shop=shop,
                            assignment_type=code,
                            defaults={
                                'primary_printer': primary_p,
                                'fallback_printer': fallback_p
                            }
                        )
                else:
                    PrinterAssignment.objects.filter(shop=shop, assignment_type=code).delete()

        AuditLog.objects.create(
            shop=shop,
            user=request.user,
            action='ROUTING_ASSIGNMENTS_UPDATED',
            resource_type='PrinterAssignment',
            resource_id=str(shop.id),
            details={'updated_by': request.user.username}
        )
        messages.success(request, "Printer routing rules saved successfully.")
        return redirect('printers:printer_assignments')

    context = {
        'shop': shop,
        'printers': printers,
        'assignment_types': assignment_types,
        'assignment_map': assignment_map,
    }
    return render(request, 'printers/printer_assignments.html', context)


@owner_required
def reassign_queued_jobs_view(request):
    """
    Reassigns unassigned QUEUED jobs to an eligible online printer.
    """
    shop = get_user_shop(request.user)
    queued_jobs = PrintJob.objects.filter(
        order__shop=shop,
        status=PrintJob.Status.QUEUED
    ).select_related('order', 'order__preference')

    reassigned_count = 0
    for job in queued_jobs:
        target = RoutingService.determine_target_printer(shop, job.order.preference)
        if target:
            RoutingService.reassign_job(job, target, user=request.user)
            reassigned_count += 1

    if reassigned_count > 0:
        messages.success(request, f"Successfully routed {reassigned_count} queued job(s) to active printers.")
    else:
        messages.info(request, "No eligible online printer was available to take queued jobs right now.")

    return redirect('orders:order_list')
