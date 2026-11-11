from django.contrib import admin
from .models import PrintDocument, PrintPreference, PricingRule, PrintOrder, PrintJob, PrintJobAttempt


@admin.register(PrintDocument)
class PrintDocumentAdmin(admin.ModelAdmin):
    list_display = ('original_filename', 'shop', 'detected_page_count', 'verified_page_count', 'encrypted_file_size', 'created_at')
    search_fields = ('original_filename', 'file_hash_sha256')


@admin.register(PrintPreference)
class PrintPreferenceAdmin(admin.ModelAdmin):
    list_display = ('color_mode', 'duplex_mode', 'paper_size', 'copies', 'page_range_type', 'total_calculated_pages')


@admin.register(PricingRule)
class PricingRuleAdmin(admin.ModelAdmin):
    list_display = ('shop', 'bw_single_rate', 'bw_double_rate', 'color_single_rate', 'color_double_rate', 'a3_bw_rate', 'a3_color_rate', 'is_active')
    list_filter = ('is_active', 'shop')


@admin.register(PrintOrder)
class PrintOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'shop', 'customer_name', 'customer_phone', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'shop', 'created_at')
    search_fields = ('order_number', 'customer_name', 'customer_phone')


@admin.register(PrintJob)
class PrintJobAdmin(admin.ModelAdmin):
    list_display = ('order', 'printer', 'status', 'assigned_at', 'dispatched_at', 'completed_at')
    list_filter = ('status', 'printer__shop')


@admin.register(PrintJobAttempt)
class PrintJobAttemptAdmin(admin.ModelAdmin):
    list_display = ('job', 'printer', 'attempt_number', 'status', 'timestamp')
