"""
URL configuration for KEP PrintGrid project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from orders import views as orders_views
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Main Website Entry
    path('', core_views.home, name='home'),

    # 1. Shop Owner Interface Dedicated Routes
    path('register-shop/', core_views.register_owner, name='register_shop'),
    path('register-shop', core_views.register_owner),
    path('shop-login/', core_views.user_login, name='shop_login'),
    path('shop-login', core_views.user_login),
    path('dashboard/', core_views.dashboard_dispatch, name='dashboard'),
    path('dashboard', core_views.dashboard_dispatch),
    path('shop/qr/', core_views.shop_qr_management, name='shop_qr_shortcut'),
    path('shop/qr', core_views.shop_qr_management),

    # 2. Customer Interface Dedicated Routes
    path('shop/<slug:slug>/', orders_views.shop_order_page, name='shop_order_page'),
    path('shop/<slug:slug>', orders_views.shop_order_page),
    path('shop/<str:shop_unique_id>/', orders_views.shop_order_page, name='shop_order_page_unique'),
    path('track-order/', orders_views.customer_track_order_lookup, name='track_order'),
    path('track-order', orders_views.customer_track_order_lookup),
    path('track-order/<str:order_number>/', orders_views.customer_track_order, name='customer_track_order'),
    path('track-order/<str:order_number>', orders_views.customer_track_order),

    # Core & Feature Module Routing
    path('', include('core.urls')),
    path('orders/', include('orders.urls')),
    path('printers/', include('printers.urls')),
    path('payments/', include('payments.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
