"""
Django Admin Configuration for GrihaStay models
"""
from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from .models import *


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'created_at']
    search_fields = ['name', 'code']


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'country', 'created_at']
    search_fields = ['name', 'code']
    list_filter = ['country']


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'state', 'created_at']
    search_fields = ['name', 'code']
    list_filter = ['state']


@admin.register(Municipality)
class MunicipalityAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'district', 'created_at']
    search_fields = ['name', 'code']
    list_filter = ['district']


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'district', 'created_at']
    search_fields = ['name']
    list_filter = ['district']


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ['name', 'municipality', 'district', 'state', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['state', 'district', 'municipality']

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_email', 'contact_phone', 'plan', 'created_at']
    search_fields = ['name', 'contact_email', 'registration_number']
    list_filter = ['plan', 'currency']


@admin.register(TenantUser)
class TenantUserAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'full_name', 'email', 'tenant', 'role', 'is_active', 'created_at']
    search_fields = ['user_name', 'email', 'full_name']
    list_filter = ['tenant', 'role', 'is_active']
    readonly_fields = ['last_login', 'created_at', 'updated_at']


@admin.register(PropertyType)
class PropertyTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(Property)
class PropertyAdmin(OSMGeoAdmin):
    list_display = ['name', 'tenant', 'property_type', 'status', 'city', 'created_at']
    search_fields = ['name', 'description', 'address']
    list_filter = ['tenant', 'property_type', 'status', 'state', 'district']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'property', 'max_occupancy', 'default_base_price', 'created_at']
    search_fields = ['name', 'slug']
    list_filter = ['property']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'room_type', 'status', 'price_override']
    search_fields = ['room_number']
    list_filter = ['room_type', 'status']


@admin.register(RatePlan)
class RatePlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'property', 'room_type', 'base_price', 'active', 'created_at']
    search_fields = ['name']
    list_filter = ['property', 'active']


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['room_type', 'dt', 'available_count', 'blocked_count', 'updated_at']
    list_filter = ['room_type', 'dt']
    date_hierarchy = 'dt'


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'nationality', 'created_at']
    search_fields = ['name', 'email', 'phone']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'property', 'room_type', 'checkin', 'checkout', 'status', 'payment_status', 'total_amount', 'created_at']
    search_fields = ['external_id']
    list_filter = ['tenant', 'property', 'status', 'payment_status', 'source']
    date_hierarchy = 'checkin'
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['booking', 'method', 'amount', 'status', 'transaction_id', 'created_at']
    search_fields = ['transaction_id']
    list_filter = ['method', 'status']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'booking', 'amount', 'tax_amount', 'issued_at']
    search_fields = ['invoice_number']
    list_filter = ['issued_at']


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'amount', 'status', 'scheduled_at', 'processed_at']
    list_filter = ['tenant', 'status']
    date_hierarchy = 'scheduled_at'


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'actor', 'action', 'created_at']
    search_fields = ['actor', 'action']
    list_filter = ['tenant', 'action']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
