from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse, Http404, FileResponse
from django.db import transaction
import os

from core.models import Shop, AuditLog
from core.decorators import owner_required, staff_or_owner_required, get_user_shop
from printers.models import Printer
from printers.services.routing_service import RoutingService
from .models import PrintOrder, PrintJob, PrintJobAttempt, PricingRule, PrintDocument
from .forms import PricingRuleForm


def shop_order_page(request, slug):
    """
    Public customer ordering page reached when scanning the shop's permanent QR code.
    Shows shop info, pause status, document uploader, PDF.js preview, preferences, and price quote.
    """
    shop = get_object_or_404(Shop, slug=slug)

    # Fetch active shop pricing
    pricing = PricingRule.objects.filter(shop=shop, is_active=True).first()
    if not pricing:
        pricing = PricingRule.objects.create(shop=shop)

    # Determine what options to offer based on shop printers capabilities
    printers = Printer.objects.filter(shop=shop, is_active=True).select_related('capability')
    has_color_printer = printers.filter(handles_color=True).exists()
    has_duplex_printer = any(getattr(p, 'capability', None) and p.capability.supports_duplex for p in printers)
    has_a3_printer = any(getattr(p, 'capability', None) and 'A3' in p.capability.supported_paper_sizes for p in printers)

    context = {
        'shop': shop,
        'pricing': pricing,
        'has_color_printer': has_color_printer,
        'has_duplex_printer': has_duplex_printer,
        'has_a3_printer': has_a3_printer,
        'connector_public_key': shop.connector_public_key,
    }
    return render(request, 'orders/shop_order_page.html', context)


def customer_track_order(request, order_number):
    """
    Public order tracking page for customer.
    """
    order = get_object_or_404(PrintOrder.objects.select_related('shop', 'preference', 'print_job'), order_number=order_number)
    context = {
        'order': order,
        'job': getattr(order, 'print_job', None),
    }
    return render(request, 'orders/customer_track_order.html', context)


@owner_required
def pricing_settings_view(request):
    """
    Shop owner pricing configuration for print services.
    """
    shop = get_user_shop(request.user)
    pricing = PricingRule.objects.filter(shop=shop).first()
    if not pricing:
        pricing = PricingRule.objects.create(shop=shop)

    if request.method == 'POST':
        form = PricingRuleForm(request.POST, instance=pricing)
        if form.is_valid():
            form.save()
            AuditLog.objects.create(
                shop=shop,
                user=request.user,
                action='PRICING_UPDATED',
                resource_type='PricingRule',
                resource_id=str(pricing.id),
                details={
                    'bw_single': str(pricing.bw_single_rate),
                    'color_single': str(pricing.color_single_rate)
                }
            )
            messages.success(request, "Printing rates updated successfully.")
            return redirect('orders:pricing_settings')
    else:
        form = PricingRuleForm(instance=pricing)

    context = {
        'shop': shop,
        'form': form,
        'pricing': pricing,
    }
    return render(request, 'orders/pricing_settings.html', context)


@staff_or_owner_required
def order_list(request):
    """
    Order management table with filtering by status, search, and date.
    """
    shop = get_user_shop(request.user)
    orders = PrintOrder.objects.filter(shop=shop).select_related('document', 'preference', 'print_job', 'print_job__printer').order_by('-created_at')

    status_filter = request.GET.get('status')
    search_query = request.GET.get('q')

    if status_filter:
        orders = orders.filter(status=status_filter)
    if search_query:
        orders = orders.filter(order_number__icontains=search_query) | orders.filter(customer_phone__icontains=search_query)

    context = {
        'shop': shop,
        'orders': orders,
        'status_choices': PrintOrder.Status.choices,
        'selected_status': status_filter,
        'search_query': search_query,
    }
    return render(request, 'orders/order_list.html', context)


@staff_or_owner_required
def order_detail(request, order_number):
    """
    Detailed inspection of a print order.
    """
    shop = get_user_shop(request.user)
    order = get_object_or_404(
        PrintOrder.objects.select_related('shop', 'document', 'preference', 'print_job', 'print_job__printer'),
        shop=shop,
        order_number=order_number
    )
    payments = order.payments.all()
    attempts = order.print_job.attempts.all() if hasattr(order, 'print_job') else []

    context = {
        'shop': shop,
        'order': order,
        'job': getattr(order, 'print_job', None),
        'payments': payments,
        'attempts': attempts,
    }
    return render(request, 'orders/order_detail.html', context)


@staff_or_owner_required
def mark_order_completed(request, order_number):
    """
    Marks order as completed and collected by customer.
    """
    shop = get_user_shop(request.user)
    order = get_object_or_404(PrintOrder, shop=shop, order_number=order_number)
    order.status = PrintOrder.Status.COMPLETED
    order.save()

    if hasattr(order, 'print_job'):
        job = order.print_job
        job.status = PrintJob.Status.PHYSICALLY_PRINTED
        job.completed_at = timezone.now()
        job.save()

    AuditLog.objects.create(
        shop=shop,
        user=request.user,
        action='ORDER_HANDOVER_COMPLETED',
        resource_type='PrintOrder',
        resource_id=str(order.id),
        details={'order_number': order.order_number, 'collected_by': order.customer_name}
    )
    messages.success(request, f"Order {order.order_number} marked as completed & handed over.")
    return redirect('orders:staff_dashboard')


@staff_or_owner_required
def staff_dashboard(request):
    """
    Streamlined dashboard for shop front-desk staff.
    """
    shop = get_user_shop(request.user)
    orders = PrintOrder.objects.filter(shop=shop).select_related('document', 'preference', 'print_job', 'print_job__printer').order_by('-created_at')

    # Quick counters
    active_jobs = orders.filter(status__in=[
        PrintOrder.Status.PAYMENT_VERIFIED,
        PrintOrder.Status.QUEUED,
        PrintOrder.Status.ASSIGNED,
        PrintOrder.Status.SENT_TO_PRINTER,
        PrintOrder.Status.PRINTING
    ])

    ready_jobs = orders.filter(status=PrintOrder.Status.COMPLETED)
    failed_jobs = orders.filter(status=PrintOrder.Status.FAILED)

    context = {
        'shop': shop,
        'active_jobs': active_jobs,
        'ready_jobs': ready_jobs[:10],
        'failed_jobs': failed_jobs[:10],
    }
    return render(request, 'orders/staff_dashboard.html', context)


@staff_or_owner_required
def authorize_retry(request, order_number):
    """
    Explicitly authorizes a print retry after hardware intervention (e.g. paper refill, clear jam).
    """
    shop = get_user_shop(request.user)
    order = get_object_or_404(PrintOrder, shop=shop, order_number=order_number)

    if not hasattr(order, 'print_job'):
        messages.error(request, "No print job associated with this order.")
        return redirect('orders:order_detail', order_number=order_number)

    job = order.print_job
    target_printer = RoutingService.determine_target_printer(shop, order.preference)

    if not target_printer:
        messages.error(request, "No active online printer capable of printing this job was found. Please ensure a printer is connected.")
        return redirect('orders:order_detail', order_number=order_number)

    with transaction.atomic():
        job.printer = target_printer
        job.status = PrintJob.Status.DISPATCHED
        job.dispatched_at = timezone.now()
        job.failure_reason = ""
        job.save()

        order.status = PrintOrder.Status.ASSIGNED
        order.save()

        PrintJobAttempt.objects.create(
            job=job,
            printer=target_printer,
            attempt_number=job.attempts.count() + 1,
            status=PrintJob.Status.DISPATCHED,
            error_message="Manual retry authorized by shop staff",
            authorized_by=request.user
        )

        AuditLog.objects.create(
            shop=shop,
            user=request.user,
            action='PRINT_JOB_RETRY_AUTHORIZED',
            resource_type='PrintJob',
            resource_id=str(job.id),
            details={'order_number': order.order_number, 'target_printer': target_printer.name}
        )

    messages.success(request, f"Retry authorized! Job dispatched to '{target_printer.name}'.")
    return redirect('orders:order_detail', order_number=order_number)


def secure_document_download(request, document_id):
    """
    Encrypted document download endpoint.
    Strictly restricted to the authorized shop connector via token validation.
    The cloud backend never decrypts document content.
    """
    token = request.GET.get('token') or request.headers.get('X-Shop-Token')
    if not token:
        raise Http404("Missing access credentials")

    doc = get_object_or_404(PrintDocument, id=document_id)
    if doc.shop.connector_auth_token != token:
        raise Http404("Unauthorized connector")

    if not doc.encrypted_file or not os.path.exists(doc.encrypted_file.path):
        raise Http404("Encrypted document file missing from storage")

    response = FileResponse(open(doc.encrypted_file.path, 'rb'), content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="encrypted_{doc.id}.bin"'
    return response
