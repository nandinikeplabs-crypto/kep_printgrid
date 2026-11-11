from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_owner, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard_dispatch, name='dashboard'),
    path('dashboard/overview/', views.owner_overview, name='owner_overview'),
    path('dashboard/qr-code/', views.shop_qr_management, name='shop_qr_management'),
    path('dashboard/qr-code/download/<str:asset_type>/', views.download_qr_asset, name='download_qr_asset'),
    path('dashboard/settings/', views.shop_settings, name='shop_settings'),
    path('dashboard/staff/', views.staff_management, name='staff_management'),
    path('dashboard/staff/remove/<uuid:staff_id>/', views.remove_staff, name='remove_staff'),
    path('dashboard/reports/', views.reports_view, name='reports'),
]
