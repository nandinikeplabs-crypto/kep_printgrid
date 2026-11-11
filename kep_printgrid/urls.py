"""
URL configuration for KEP PrintGrid project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from orders import views as orders_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Permanent QR Code destination: https://domain/shop/<shop-unique-slug>/
    path('shop/<slug:slug>/', orders_views.shop_order_page, name='shop_order_page'),

    # Core (Auth, Dashboards, QR, Settings, Staff, Reports)
    path('', include('core.urls')),

    # Orders (Ordering API, Tracking, Order Management, Pricing)
    path('orders/', include('orders.urls')),

    # Printers & Local Connector (Printer Management, Spooler Sync, Heartbeat)
    path('printers/', include('printers.urls')),

    # Payments (Razorpay Integration, Verification, Webhooks, Refunds)
    path('payments/', include('payments.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
