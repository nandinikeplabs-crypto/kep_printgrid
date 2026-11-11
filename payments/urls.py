from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('api/create-order/', views.CreatePaymentOrderAPIView.as_view(), name='api_create_payment_order'),
    path('api/verify/', views.VerifyPaymentAPIView.as_view(), name='api_verify_payment'),
    path('api/webhook/', views.PaymentWebhookAPIView.as_view(), name='api_payment_webhook'),
    path('refund/<str:order_number>/', views.initiate_refund_view, name='initiate_refund'),
]
