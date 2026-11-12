from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q
from decimal import Decimal
from datetime import timedelta
import os
from django.http import FileResponse, Http404

from .models import Shop, ShopStaff, ShopQRCode, AuditLog, User
from .forms import ShopOwnerRegistrationForm, LoginForm, ShopSettingsForm, StaffCreateForm
from .decorators import owner_required, staff_or_owner_required, get_user_shop
from core.services.qr_service import generate_shop_qr_code
from orders.models import PrintOrder, PrintJob
from printers.models import Printer


def home(request):
    """
    Landing page for KEP PrintGrid.
    """
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    return render(request, 'core/home.html')


def qr_scanner_page(request):
    """
    Dedicated in-browser QR Code scanner page.
    Allows customers to scan a counter QR stand using laptop webcam or phone camera.
    """
    return render(request, 'core/scanner.html', {'is_customer_view': True})


def register_owner(request):
    """
    Registration flow for shop owners.
    """
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = ShopOwnerRegistrationForm(request.POST)
        if form.is_valid():
            user, shop = form.save()
            login(request, user)
            AuditLog.objects.create(
                shop=shop,
                user=user,
                action='SHOP_REGISTERED',
                resource_type='Shop',
                resource_id=str(shop.id),
                ip_address=request.META.get('REMOTE_ADDR'),
                details={'shop_name': shop.name, 'slug': shop.slug}
            )
            messages.success(request, f"Welcome to KEP PrintGrid! Your shop '{shop.name}' is now active with unique Shop ID: {shop.shop_code}.")
            return redirect('dashboard')
    else:
        form = ShopOwnerRegistrationForm()

    return render(request, 'core/register.html', {'form': form})


def user_login(request):
    """
    Unified login view for owners, staff, and registered users.
    """
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['authenticated_user']
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect('core:dashboard')
    else:
        form = LoginForm()

    return render(request, 'core/login.html', {'form': form})


def user_logout(request):
    """
    Terminates the user session.
    """
    logout(request)
    messages.info(request, "You have been logged out safely.")
    return redirect('core:login')


@staff_or_owner_required
def dashboard_dispatch(request):
    """
    Directs the user to the correct dashboard according to their role.
    """
    if request.user.is_owner() or request.user.is_superuser:
        return redirect('core:owner_overview')
    elif request.user.is_staff_member():
        return redirect('orders:staff_dashboard')
    return redirect('core:home')


@owner_required
def owner_overview(request):
    """
    Shop Owner Overview Dashboard with live metrics, printers status and recent orders.
    """
    shop = get_user_shop(request.user)
    if not shop:
        messages.error(request, "No registered shop found for this account.")
        return redirect('core:register')

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Orders queries
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
    completed_orders = shop_orders.filter(status=PrintOrder.Status.COMPLETED).count()
    failed_orders = shop_orders.filter(status=PrintOrder.Status.FAILED).count()

    # Revenue metrics
    today_revenue = shop_orders.filter(
        created_at__gte=today_start,
        status__in=[
            PrintOrder.Status.PAYMENT_VERIFIED,
            PrintOrder.Status.QUEUED,
            PrintOrder.Status.ASSIGNED,
            PrintOrder.Status.SENT_TO_PRINTER,
            PrintOrder.Status.PRINTING,
            PrintOrder.Status.COMPLETED
        ]
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')

    total_revenue = shop_orders.filter(
        status__in=[
            PrintOrder.Status.PAYMENT_VERIFIED,
            PrintOrder.Status.QUEUED,
            PrintOrder.Status.ASSIGNED,
            PrintOrder.Status.SENT_TO_PRINTER,
            PrintOrder.Status.PRINTING,
            PrintOrder.Status.COMPLETED
        ]
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')

    # Printers metrics
    shop_printers = Printer.objects.filter(shop=shop)
    online_printers = shop_printers.filter(is_online=True, is_active=True).count()
    offline_printers = shop_printers.filter(Q(is_online=False) | Q(is_active=False)).count()

    recent_orders = shop_orders.select_related('document', 'preference').order_by('-created_at')[:10]

    context = {
        'shop': shop,
        'total_orders': total_orders,
        'today_orders': today_orders,
        'pending_orders': pending_orders,
        'printing_orders': printing_orders,
        'completed_orders': completed_orders,
        'failed_orders': failed_orders,
        'today_revenue': today_revenue,
        'total_revenue': total_revenue,
        'online_printers': online_printers,
        'offline_printers': offline_printers,
        'shop_printers': shop_printers,
        'recent_orders': recent_orders,
    }
    return render(request, 'core/owner_overview.html', context)


@owner_required
def shop_qr_management(request):
    """
    Shop Permanent QR Code display, regeneration, physical printer mapping, and download options.
    """
    from printers.models import Printer

    shop = get_user_shop(request.user)
    qr_record = getattr(shop, 'qr_code', None)

    current_url = shop.order_page_url
    if not qr_record or not qr_record.qr_code_image or getattr(qr_record, 'qr_target_url', '') != current_url:
        qr_record = generate_shop_qr_code(shop)

    # Ensure QR code has an assigned printer if printers exist
    if not qr_record.assigned_printer:
        default_p = shop.printers.filter(is_default=True).first() or shop.printers.first()
        if default_p:
            qr_record.assigned_printer = default_p
            qr_record.save(update_fields=['assigned_printer', 'updated_at'])

    if request.method == 'POST':
        if 'regenerate' in request.POST:
            qr_record = generate_shop_qr_code(shop)
            AuditLog.objects.create(
                shop=shop,
                user=request.user,
                action='QR_REGENERATED',
                resource_type='ShopQRCode',
                resource_id=str(qr_record.id),
                details={'target_url': shop.order_page_url}
            )
            messages.success(request, "QR Code assets re-rendered successfully!")
            return redirect('core:shop_qr_management')

        elif 'assign_printer' in request.POST:
            printer_id = request.POST.get('assigned_printer_id')
            if printer_id:
                printer = get_object_or_404(Printer, id=printer_id, shop=shop)
                qr_record.assigned_printer = printer
                qr_record.save(update_fields=['assigned_printer', 'updated_at'])
                AuditLog.objects.create(
                    shop=shop,
                    user=request.user,
                    action='PRINTER_ASSIGNED_TO_QR',
                    resource_type='ShopQRCode',
                    resource_id=str(qr_record.id),
                    details={'printer_id': str(printer.id), 'printer_name': printer.name, 'printer_code': printer.printer_code}
                )
                messages.success(request, f"Printer '{printer.name}' [ID: {printer.printer_code}] permanently mapped to this QR code!")
            else:
                qr_record.assigned_printer = None
                qr_record.save(update_fields=['assigned_printer', 'updated_at'])
                messages.info(request, "QR code will now dynamically route to the shop's default printer.")
            return redirect('core:shop_qr_management')

    poster_pdf_path = os.path.join('media', 'qr_codes', f"shop_qr_{shop.slug}_poster.pdf")
    has_poster_pdf = os.path.exists(poster_pdf_path)

    context = {
        'shop': shop,
        'qr_record': qr_record,
        'shop_printers': shop.printers.all(),
        'assigned_printer': qr_record.assigned_printer,
        'has_poster_pdf': has_poster_pdf,
    }
    return render(request, 'core/shop_qr_management.html', context)


@owner_required
def download_qr_asset(request, asset_type):
    """
    Provides secure download for the shop permanent QR PNG or printable PDF stand.
    """
    shop = get_user_shop(request.user)
    if asset_type == 'png':
        current_url = shop.order_page_url
        qr_path = os.path.join('media', 'qr_codes', f"shop_qr_{shop.slug}.png")
        if not os.path.exists(qr_path) or getattr(getattr(shop, 'qr_code', None), 'qr_target_url', '') != current_url:
            generate_shop_qr_code(shop)
        return FileResponse(open(qr_path, 'rb'), as_attachment=True, filename=f"{shop.slug}_permanent_qr.png")
    elif asset_type == 'pdf':
        current_url = shop.order_page_url
        pdf_path = os.path.join('media', 'qr_codes', f"shop_qr_{shop.slug}_poster.pdf")
        if not os.path.exists(pdf_path) or getattr(getattr(shop, 'qr_code', None), 'qr_target_url', '') != current_url:
            generate_shop_qr_code(shop)
        return FileResponse(open(pdf_path, 'rb'), as_attachment=True, filename=f"{shop.slug}_display_poster.pdf")
    raise Http404("Asset type not found")


@owner_required
def shop_settings(request):
    """
    Shop configuration: profile details, pause/resume ordering switch.
    """
    shop = get_user_shop(request.user)

    if request.method == 'POST':
        form = ShopSettingsForm(request.POST, instance=shop)
        if form.is_valid():
            old_status = shop.is_accepting_orders
            updated_shop = form.save()
            new_status = updated_shop.is_accepting_orders

            if old_status != new_status:
                AuditLog.objects.create(
                    shop=shop,
                    user=request.user,
                    action='ORDERING_TOGGLED',
                    resource_type='Shop',
                    resource_id=str(shop.id),
                    details={'is_accepting_orders': new_status}
                )

            messages.success(request, "Shop settings updated successfully.")
            return redirect('core:shop_settings')
    else:
        form = ShopSettingsForm(instance=shop)

    context = {
        'shop': shop,
        'form': form,
    }
    return render(request, 'core/shop_settings.html', context)


@owner_required
def staff_management(request):
    """
    Manage shop operators and granular staff permissions.
    """
    shop = get_user_shop(request.user)
    staff_members = ShopStaff.objects.filter(shop=shop).select_related('user')

    if request.method == 'POST':
        form = StaffCreateForm(request.POST)
        if form.is_valid():
            staff = form.save(shop=shop)
            AuditLog.objects.create(
                shop=shop,
                user=request.user,
                action='STAFF_CREATED',
                resource_type='ShopStaff',
                resource_id=str(staff.id),
                details={'username': staff.user.username}
            )
            messages.success(request, f"Staff member '{staff.user.get_full_name() or staff.user.username}' added.")
            return redirect('core:staff_management')
    else:
        form = StaffCreateForm()

    context = {
        'shop': shop,
        'staff_members': staff_members,
        'form': form,
    }
    return render(request, 'core/staff_management.html', context)


@owner_required
def remove_staff(request, staff_id):
    """
    Deactivates or removes a staff member.
    """
    shop = get_user_shop(request.user)
    staff = get_object_or_404(ShopStaff, id=staff_id, shop=shop)
    user = staff.user
    user.is_active = False
    user.save()
    staff.delete()

    AuditLog.objects.create(
        shop=shop,
        user=request.user,
        action='STAFF_REMOVED',
        resource_type='ShopStaff',
        resource_id=str(staff_id),
        details={'username': user.username}
    )
    messages.info(request, f"Staff account '{user.username}' removed.")
    return redirect('core:staff_management')


@owner_required
def reports_view(request):
    """
    Business performance & printing operations analytics report.
    """
    shop = get_user_shop(request.user)
    orders = PrintOrder.objects.filter(shop=shop)

    now = timezone.now()
    days_data = []
    for i in range(6, -1, -1):
        day = (now - timedelta(days=i)).date()
        day_orders = orders.filter(created_at__date=day)
        day_rev = day_orders.filter(
            status__in=[
                PrintOrder.Status.PAYMENT_VERIFIED,
                PrintOrder.Status.QUEUED,
                PrintOrder.Status.ASSIGNED,
                PrintOrder.Status.SENT_TO_PRINTER,
                PrintOrder.Status.PRINTING,
                PrintOrder.Status.COMPLETED
            ]
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')

        days_data.append({
            'date': day.strftime('%d %b'),
            'orders_count': day_orders.count(),
            'revenue': float(day_rev)
        })

    # Mode breakdown
    bw_count = orders.filter(preference__color_mode='BW').count()
    color_count = orders.filter(preference__color_mode='COLOR').count()

    context = {
        'shop': shop,
        'days_data': days_data,
        'bw_count': bw_count,
        'color_count': color_count,
        'total_orders': orders.count(),
    }
    return render(request, 'core/reports.html', context)
