"""
URL Configuration for core app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import register_tenant, login, health_check, CustomTokenObtainPairView
from .viewsets import *

# Create router for ViewSets
router = DefaultRouter()

# Location routes
router.register(r'countries', CountryViewSet, basename='country')
router.register(r'states', StateViewSet, basename='state')
router.register(r'districts', DistrictViewSet, basename='district')
router.register(r'municipalities', MunicipalityViewSet, basename='municipality')
router.register(r'cities', CityViewSet, basename='city')

# Community routes
router.register(r'communities', CommunityViewSet, basename='community')
router.register(r'community-media', CommunityMediaViewSet, basename='community-media')

# Tenant & User routes
router.register(r'tenants', TenantViewSet, basename='tenant')
router.register(r'users', TenantUserViewSet, basename='user')

# Property routes
router.register(r'property-types', PropertyTypeViewSet, basename='property-type')
router.register(r'amenities', AmenityViewSet, basename='amenity')
router.register(r'properties', PropertyViewSet, basename='property')
router.register(r'house-rules', HouseRuleViewSet, basename='house-rule')

# Room routes
router.register(r'room-types', RoomTypeViewSet, basename='room-type')
router.register(r'rooms', RoomViewSet, basename='room')
router.register(r'room-images', RoomImageViewSet, basename='room-image')

# Rate plan routes
router.register(r'rate-plans', RatePlanViewSet, basename='rate-plan')
router.register(r'rate-plan-rules', RatePlanRuleViewSet, basename='rate-plan-rule')

# Inventory routes
router.register(r'inventory', InventoryViewSet, basename='inventory')
router.register(r'channel-allocations', ChannelAllocationViewSet, basename='channel-allocation')

# Guest routes
router.register(r'guests', GuestViewSet, basename='guest')
router.register(r'tenant-guest-profiles', TenantGuestProfileViewSet, basename='tenant-guest-profile')

# Booking routes
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'booking-items', BookingItemViewSet, basename='booking-item')
router.register(r'booking-guest-info', BookingGuestInfoViewSet, basename='booking-guest-info')

# Payment routes
router.register(r'payments', PaymentViewSet, basename='payment')

# Invoice & Payout routes
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'payouts', PayoutViewSet, basename='payout')

# Webhook & Audit routes
router.register(r'webhooks', WebhookRegistrationViewSet, basename='webhook')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')

urlpatterns = [
    # Health check
    path('health/', health_check, name='health-check'),
    
    # Authentication endpoints
    path('auth/register/', register_tenant, name='register'),
    path('auth/login/', login, name='login'),
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Include router URLs
    path('', include(router.urls)),
]
