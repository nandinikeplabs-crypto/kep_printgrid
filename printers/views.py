import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction

from core.decorators import owner_required, get_user_shop
from core.models import AuditLog
from .models import Printer, PrinterCapability, PrinterAssignment
from .forms import PrinterForm
from orders.models import PrintJob
from printers.services.routing_service import RoutingService
from connector.spooler.windows_spooler import WindowsSpooler
from printers.services.test_print_service import generate_printer_test_page

logger = logging.getLogger(__name__)


@owner_required
def printer_list(request):
    """
    Overview of all printers configured for the shop with live status,
    detected Windows spooler queues, QR code mapping, and test print actions.
    """
    shop = get_user_shop(request.user)
    printers = Printer.objects.filter(shop=shop).select_related('capability')
    qr_record = getattr(shop, 'qr_code', None)

    # Detect installed Windows printers in real time
    detected_printers = []
    try:
        spooler = WindowsSpooler()
        detected_printers = spooler.get_installed_printers()
    except Exception as e:
        logger.warning(f"Windows printer auto-detection notice: {e}")

    # Mark which detected printers are already registered for this shop
    registered_system_names = set(printers.values_list('system_printer_name', flat=True))
    for dp in detected_printers:
        dp['is_registered'] = dp['system_name'] in registered_system_names

    # If QR code has no printer assigned yet, auto-assign shop default printer
    if qr_record and not qr_record.assigned_printer:
        default_p = printers.filter(is_default=True).first() or printers.first()
        if default_p:
            qr_record.assigned_printer = default_p
            qr_record.save(update_fields=['assigned_printer', 'updated_at'])

    context = {
        'shop': shop,
        'printers': printers,
        'qr_record': qr_record,
        'detected_printers': detected_printers,
    }
    return render(request, 'printers/printer_list.html', context)


@owner_required
def printer_register_detected(request):
    """
    Quick 1-click registration for an auto-detected or template printer.
    """
    shop = get_user_shop(request.user)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        system_name = request.POST.get('system_printer_name', '').strip() or name
        model_name = request.POST.get('model_name', '').strip() or name
        handles_color = request.POST.get('handles_color') == '1' or any(k in name.lower() for k in ['color', 'tank', 'deskjet', 'inkjet'])
        handles_bw = True
        set_default = request.POST.get('set_default') == '1' or not Printer.objects.filter(shop=shop).exists()
        assign_to_qr = request.POST.get('assign_to_qr') == '1' or set_default

        with transaction.atomic():
            if set_default:
                Printer.objects.filter(shop=shop).update(is_default=False)

            printer, created = Printer.objects.update_or_create(
                shop=shop,
                system_printer_name=system_name,
                defaults={
                    'name': name or system_name,
                    'model_name': model_name,
                    'handles_bw': handles_bw,
                    'handles_color': handles_color,
                    'is_online': True,
                    'is_active': True,
                    'is_default': set_default,
                    'last_status_message': 'Ready'
                }
            )

            is_a3 = 'a3' in name.lower() or 'wide' in name.lower()
            paper_sizes = ['A4', 'A3'] if is_a3 else ['A4', 'A5', 'LETTER']

            PrinterCapability.objects.update_or_create(
                printer=printer,
                defaults={
                    'supports_bw': True,
                    'supports_color': handles_color,
                    'supports_duplex': True,
                    'supported_paper_sizes': paper_sizes,
                    'supports_landscape': True,
                    'dpi': 1200,
                }
            )

            if assign_to_qr:
                qr_record = getattr(shop, 'qr_code', None)
                if qr_record:
                    qr_record.assigned_printer = printer
                    qr_record.save(update_fields=['assigned_printer', 'updated_at'])

            AuditLog.objects.create(
                shop=shop,
                user=request.user,
                action='PRINTER_REGISTERED',
                resource_type='Printer',
                resource_id=str(printer.id),
                details={
                    'name': printer.name,
                    'printer_code': printer.printer_code,
                    'queue': printer.system_printer_name,
                    'mapped_to_qr': assign_to_qr
                }
            )

        messages.success(
            request,
            f"Printer '{printer.name}' [ID: {printer.printer_code}] registered successfully!"
            + (" Permanently mapped to your Shop QR code." if assign_to_qr else "")
        )
    return redirect('printers:printer_list')


@owner_required
def printer_test_print(request, printer_id):
    """
    Sends an authentic physical hardware verification test page to the selected printer.
    """
    shop = get_user_shop(request.user)
    printer = get_object_or_404(Printer, id=printer_id, shop=shop)

    try:
        test_pdf = generate_printer_test_page(shop, printer)
        spooler = WindowsSpooler()
        prefs = {
            'color_mode': 'COLOR' if printer.handles_color else 'BW',
            'duplex_mode': 'SINGLE',
            'copies': 1,
            'paper_size': 'A4'
        }
        res = spooler.submit_print_job(printer.system_printer_name, test_pdf, prefs)

        AuditLog.objects.create(
            shop=shop,
            user=request.user,
            action='PRINTER_TEST_PRINT',
            resource_type='Printer',
            resource_id=str(printer.id),
            details={
                'printer_name': printer.name,
                'printer_code': printer.printer_code,
                'system_queue': printer.system_printer_name,
                'spooler_result': res
            }
        )

        if res.get('success', False):
            messages.success(
                request,
                f"Test print sent to '{printer.name}' [Queue: {printer.system_printer_name}]! (Spooler ID: {res.get('os_job_id', 'ACK')}). Check printer paper tray."
            )
        else:
            messages.warning(
                request,
                f"Test print dispatched with notice: {res.get('message', 'Spooler warning')}"
            )
    except Exception as e:
        messages.error(request, f"Could not dispatch test print: {str(e)}")

    referer = request.META.get('HTTP_REFERER')
    if referer and ('printers' in referer or 'qr-code' in referer):
        return redirect(referer)
    return redirect('printers:printer_list')


@owner_required
def printer_assign_to_qr(request, printer_id):
    """
    1-click action: Maps the chosen printer to the shop's counter QR code.
    """
    shop = get_user_shop(request.user)
    printer = get_object_or_404(Printer, id=printer_id, shop=shop)
    qr_record = getattr(shop, 'qr_code', None)
    if qr_record:
        qr_record.assigned_printer = printer
        qr_record.save(update_fields=['assigned_printer', 'updated_at'])

        AuditLog.objects.create(
            shop=shop,
            user=request.user,
            action='PRINTER_MAPPED_TO_QR',
            resource_type='ShopQRCode',
            resource_id=str(qr_record.id),
            details={'printer_id': str(printer.id), 'printer_name': printer.name, 'printer_code': printer.printer_code}
        )
        messages.success(request, f"'{printer.name}' [ID: {printer.printer_code}] is now permanently assigned to your Shop QR code!")
    else:
        messages.error(request, "Shop QR code record not found.")

    referer = request.META.get('HTTP_REFERER')
    if referer and ('printers' in referer or 'qr-code' in referer):
        return redirect(referer)
    return redirect('printers:printer_list')


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


@owner_required
def printer_create(request):
    """
    Manually add a new printer (e.g. HP Smart Tank 530) to the shop fleet.
    """
    shop = get_user_shop(request.user)
    if request.method == 'POST':
        form = PrinterForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                printer = form.save(commit=False)
                printer.shop = shop
                if printer.is_default:
                    Printer.objects.filter(shop=shop).update(is_default=False)
                printer.save()

                paper_sizes = form.cleaned_data.get('supported_paper_sizes') or ['A4']
                PrinterCapability.objects.update_or_create(
                    printer=printer,
                    defaults={
                        'supports_bw': printer.handles_bw,
                        'supports_color': printer.handles_color,
                        'supports_duplex': form.cleaned_data.get('supports_duplex', True),
                        'supported_paper_sizes': list(paper_sizes),
                        'supports_landscape': True,
                        'dpi': form.cleaned_data.get('dpi', 1200),
                    }
                )

                AuditLog.objects.create(
                    shop=shop,
                    user=request.user,
                    action='PRINTER_CREATED',
                    resource_type='Printer',
                    resource_id=str(printer.id),
                    details={'name': printer.name, 'model': printer.model_name}
                )
                messages.success(request, f"Printer '{printer.name}' added successfully to your shop!")
                return redirect('printers:printer_list')
    else:
        prefill = request.GET.get('preset')
        initial = {}
        if prefill == 'hp_smart_tank_530':
            initial = {
                'name': 'HP Smart Tank 530',
                'system_printer_name': 'HP Smart Tank 530 series',
                'model_name': 'HP Smart Tank 530 All-in-One (Product No: 4SB24A)',
                'handles_bw': True,
                'handles_color': True,
                'is_online': True,
                'is_active': True,
                'supports_duplex': True,
                'supported_paper_sizes': ['A4', 'A5', 'B5', 'LETTER', 'LEGAL', 'ENVELOPE'],
                'dpi': 1200
            }
        form = PrinterForm(initial=initial)

    return render(request, 'printers/printer_form.html', {'form': form, 'shop': shop, 'is_create': True})


@owner_required
def printer_edit(request, printer_id):
    """
    Edit an existing printer configuration.
    """
    shop = get_user_shop(request.user)
    printer = get_object_or_404(Printer, id=printer_id, shop=shop)
    cap = getattr(printer, 'capability', None)

    if request.method == 'POST':
        form = PrinterForm(request.POST, instance=printer)
        if form.is_valid():
            with transaction.atomic():
                printer = form.save(commit=False)
                if printer.is_default:
                    Printer.objects.filter(shop=shop).exclude(id=printer.id).update(is_default=False)
                printer.save()

                paper_sizes = form.cleaned_data.get('supported_paper_sizes') or ['A4']
                PrinterCapability.objects.update_or_create(
                    printer=printer,
                    defaults={
                        'supports_bw': printer.handles_bw,
                        'supports_color': printer.handles_color,
                        'supports_duplex': form.cleaned_data.get('supports_duplex', True),
                        'supported_paper_sizes': list(paper_sizes),
                        'supports_landscape': True,
                        'dpi': form.cleaned_data.get('dpi', 1200),
                    }
                )

                messages.success(request, f"Printer '{printer.name}' details updated successfully.")
                return redirect('printers:printer_list')
    else:
        initial = {}
        if cap:
            initial['supports_duplex'] = cap.supports_duplex
            initial['supported_paper_sizes'] = cap.supported_paper_sizes
            initial['dpi'] = cap.dpi
        form = PrinterForm(instance=printer, initial=initial)

    return render(request, 'printers/printer_form.html', {'form': form, 'shop': shop, 'printer': printer, 'is_create': False})


@owner_required
def printer_delete(request, printer_id):
    """
    Remove a printer from the shop fleet.
    """
    shop = get_user_shop(request.user)
    printer = get_object_or_404(Printer, id=printer_id, shop=shop)
    name = printer.name
    printer.delete()
    messages.warning(request, f"Printer '{name}' has been removed from your shop.")
    return redirect('printers:printer_list')

