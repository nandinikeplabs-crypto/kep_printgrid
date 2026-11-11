from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Shop, ShopStaff, ShopQRCode, AuditLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role & Profile', {'fields': ('role', 'phone_number')}),
    )
    list_display = ('username', 'email', 'role', 'phone_number', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'owner', 'phone', 'is_accepting_orders', 'connector_last_seen', 'created_at')
    search_fields = ('name', 'slug', 'email', 'phone')
    list_filter = ('is_accepting_orders', 'created_at')


@admin.register(ShopStaff)
class ShopStaffAdmin(admin.ModelAdmin):
    list_display = ('user', 'shop', 'can_manage_printers', 'can_authorize_retries', 'can_manage_pricing')
    list_filter = ('shop', 'can_manage_printers', 'can_authorize_retries')


@admin.register(ShopQRCode)
class ShopQRCodeAdmin(admin.ModelAdmin):
    list_display = ('shop', 'qr_target_url', 'created_at')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'shop', 'user', 'resource_type', 'resource_id', 'created_at')
    list_filter = ('action', 'resource_type', 'created_at')
    search_fields = ('action', 'resource_type', 'resource_id')
