from django.contrib import admin
from .models import Payment, Refund


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('gateway_order_id', 'gateway_payment_id', 'order', 'amount', 'currency', 'status', 'verified_at', 'created_at')
    list_filter = ('status', 'gateway_name', 'created_at')
    search_fields = ('gateway_order_id', 'gateway_payment_id', 'idempotency_key')


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('payment', 'amount', 'status', 'authorized_by', 'created_at')
    list_filter = ('status', 'created_at')
