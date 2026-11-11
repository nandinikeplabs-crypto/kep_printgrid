from django.urls import path
from . import views
from . import api_views

app_name = 'orders'

urlpatterns = [
    # Dashboard & operations views
    path('list/', views.order_list, name='order_list'),
    path('detail/<str:order_number>/', views.order_detail, name='order_detail'),
    path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('pricing-settings/', views.pricing_settings_view, name='pricing_settings'),
    path('retry/<str:order_number>/', views.authorize_retry, name='authorize_retry'),
    path('mark-completed/<str:order_number>/', views.mark_order_completed, name='mark_completed'),

    # Public customer tracking
    path('track/<str:order_number>/', views.customer_track_order, name='customer_track_order'),

    # Public Customer Ordering API endpoints
    path('api/quote/', api_views.QuoteAPIView.as_view(), name='api_quote'),
    path('api/upload/', api_views.UploadEncryptedDocumentAPIView.as_view(), name='api_upload'),
    path('api/create/', api_views.CreatePrintOrderAPIView.as_view(), name='api_create_order'),
    path('api/status/<str:order_number>/', api_views.OrderStatusAPIView.as_view(), name='api_order_status'),

    # Authorized connector encrypted document download
    path('api/document/<uuid:document_id>/download/', views.secure_document_download, name='secure_document_download'),
]
