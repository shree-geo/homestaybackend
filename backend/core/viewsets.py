"""
DRF ViewSets for GrihaStay application
"""
from uuid import UUID

from django.http import request
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from .models import *
from .serializers import *
from .permissions import *


def get_tenant_from_token(request):
    """Helper to extract tenant from JWT token"""
    if hasattr(request, 'auth') and request.auth:
        tenant_id = request.auth.get('tenant_id')
        if tenant_id:
            return Tenant.objects.filter(id=tenant_id).first()
    return None


# ===== Location ViewSets =====

class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'created_at']


class StateViewSet(viewsets.ModelViewSet):
    queryset = State.objects.all()
    serializer_class = StateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['country']
    search_fields = ['name', 'code']


class DistrictViewSet(viewsets.ModelViewSet):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['state']
    search_fields = ['name', 'code']


class MunicipalityViewSet(viewsets.ModelViewSet):
    queryset = Municipality.objects.all()
    serializer_class = MunicipalitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['district']
    search_fields = ['name', 'code']


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['district']
    search_fields = ['name']

class MultiMediaViewSet(viewsets.ModelViewSet):
    queryset = Multimedia.objects.all()
    serializer_class = MultimediaSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        user = getattr(self.request, "user", None)
        if not (user and user.is_authenticated):
            return Multimedia.objects.none()

        tenant = get_tenant_from_token(self.request)
        if tenant:
            return Multimedia.objects.filter(created_by__tenant=tenant)
        return Multimedia.objects.none()


# ===== Community ViewSets =====

class CommunityViewSet(viewsets.ModelViewSet):
    queryset = Community.objects.all()
    serializer_class = CommunitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['state', 'district', 'municipality']
    search_fields = ['name', 'description']

# ===== Tenant & User ViewSets =====

class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated, IsTenantOwner]
    
    def get_queryset(self):
        # Users can only see their own tenant
        tenant = get_tenant_from_token(self.request)
        if tenant:
            return Tenant.objects.filter(id=tenant.id)
        return Tenant.objects.none()


class TenantUserViewSet(viewsets.ModelViewSet):
    queryset = TenantUser.objects.all()
    permission_classes = [IsTenantUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['role', 'is_active']
    search_fields = ['user_name', 'email', 'full_name']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TenantUserCreateSerializer
        return TenantUserSerializer
    
    def get_queryset(self):
        # Users can only see users from their own tenant
        tenant = get_tenant_from_token(self.request)
        if tenant:
            return TenantUser.objects.filter(tenant=tenant)
        return TenantUser.objects.none()

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsTenantOwner()]
        return [IsTenantUser()]

    def perform_create(self, serializer):
        tenant = get_tenant_from_token(self.request)
        serializer.save(tenant=tenant)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user information"""
        if hasattr(request, 'auth') and request.auth:
            user_id = request.auth.get('user_id')
            if user_id:
                try:
                    user_id = UUID(request.auth.get('user_id'))
                except (TypeError, ValueError):
                    return Response({'error': 'Invalid user id'}, status=400)

                user = get_object_or_404(TenantUser, id=user_id)
                serializer = self.get_serializer(user)
                return Response(serializer.data)
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


# ===== Property ViewSets =====

class PropertyTypeViewSet(viewsets.ModelViewSet):
    queryset = PropertyType.objects.all()
    serializer_class = PropertyTypeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']


class AmenityViewSet(viewsets.ModelViewSet):
    queryset = Amenity.objects.all()
    serializer_class = AmenitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']


class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [BelongsToTenant]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'property_type', 'state', 'district', 'city', 'community']
    search_fields = ['name', 'description', 'address']
    ordering_fields = ['name', 'created_at']
    
    def get_queryset(self):
        tenant = get_tenant_from_token(self.request)
        if tenant:
            return Property.objects.filter(tenant=tenant)
        return Property.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)


# ===== House Rules ViewSets =====
class HouseRuleViewSet(viewsets.ModelViewSet):
    serializer_class = HouseRuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Only rules belonging to properties of current tenant
        """
        return HouseRule.objects.filter(
            property__tenant=self.request.user.tenant
        ).order_by('order')

    def perform_create(self, serializer):
        property_id = serializer.validated_data['property'].id
        Property.objects.get(
            id=property_id,
            tenant=self.request.user.tenant
        )

        serializer.save()
    @action(
        detail=False,
        methods=['post'],
        url_path='bulk-create'
    )
    def bulk_create(self, request):
        serializer = HouseRuleBulkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rules = serializer.validated_data['rules']

        for rule in rules:
            Property.objects.get(
                id=rule['property'].id,
                tenant=request.user.tenant
            )

        instances = serializer.save()

        return Response(
            HouseRuleSerializer(instances, many=True).data,
            status=status.HTTP_201_CREATED
        )

    @action(
        detail=False,
        methods=['get'],
        url_path='by-property/(?P<property_id>[^/.]+)'
    )
    def by_property(self, request, property_id=None):
        rules = self.get_queryset().filter(property_id=property_id)
        serializer = self.get_serializer(rules, many=True)
        return Response(serializer.data)


# ===== Room ViewSets =====

class RoomTypeViewSet(viewsets.ModelViewSet):
    queryset = RoomType.objects.all()
    serializer_class = RoomTypeSerializer
    permission_classes = [IsAuthenticated, BelongsToTenant]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['property']
    search_fields = ['name', 'description']
    
    def get_queryset(self):
        tenant = get_tenant_from_token(self.request)
        if tenant:
            return RoomType.objects.filter(property__tenant=tenant)
        return RoomType.objects.none()


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated, BelongsToTenant]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['room_type', 'status']
    search_fields = ['room_number']
    
    def get_queryset(self):
        tenant = get_tenant_from_token(self.request)
        if tenant:
            return Room.objects.filter(room_type__property__tenant=tenant)
        return Room.objects.none()

# ===== Rate Plan ViewSets =====

class RatePlanViewSet(viewsets.ModelViewSet):
    queryset = RatePlan.objects.all()
    serializer_class = RatePlanSerializer
    permission_classes = [IsAuthenticated, BelongsToTenant]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['property', 'room_type', 'active']
    search_fields = ['name', 'description']
    
    def get_queryset(self):
        tenant = get_tenant_from_token(self.request)
        if tenant:
            return RatePlan.objects.filter(property__tenant=tenant)
        return RatePlan.objects.none()


class RatePlanRuleViewSet(viewsets.ModelViewSet):
    queryset = RatePlanRule.objects.all()
    serializer_class = RatePlanRuleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['rate_plan']
    
    def get_queryset(self):
        tenant = get_tenant_from_token(self.request)
        if tenant:
            return RatePlanRule.objects.filter(rate_plan__property__tenant=tenant)
        return RatePlanRule.objects.none()


# ===== Inventory ViewSets =====

class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated, BelongsToTenant]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['room_type', 'dt']
    ordering_fields = ['dt']
    
    def get_queryset(self):
        print(">>> get_queryset reached")

        tenant = get_tenant_from_token(self.request)
        if tenant:
            return Inventory.objects.filter(room_type__property__tenant=tenant)
        return Inventory.objects.none()


class ChannelAllocationViewSet(viewsets.ModelViewSet):
    queryset = ChannelAllocation.objects.all()
    serializer_class = ChannelAllocationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['room_type', 'channel_code']


# ===== Guest ViewSets =====

class GuestViewSet(viewsets.ModelViewSet):
    queryset = Guest.objects.all()
    serializer_class = GuestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'email', 'phone']


class TenantGuestProfileViewSet(viewsets.ModelViewSet):
    queryset = TenantGuestProfile.objects.all()
    serializer_class = TenantGuestProfileSerializer
    permission_classes = [IsAuthenticated, BelongsToTenant]
    filter_backends = [filters.SearchFilter]
    search_fields = ['display_name', 'notes']
    
    def get_queryset(self):
        tenant = get_tenant_from_token(self.request)
        if tenant:
            return TenantGuestProfile.objects.filter(tenant=tenant)
        return TenantGuestProfile.objects.none()
    
    def perform_create(self, serializer):
        tenant = get_tenant_from_token(self.request)
        serializer.save(tenant=tenant)


# ===== Booking ViewSets =====

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated, BelongsToTenant]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['property', 'room_type', 'status', 'payment_status', 'source']
    search_fields = ['external_id']
    ordering_fields = ['checkin', 'checkout', 'created_at']
    
    def get_queryset(self):
        tenant = get_tenant_from_token(self.request)
        if tenant:
            return Booking.objects.filter(tenant=tenant)
        return Booking.objects.none()
    
    def perform_create(self, serializer):
        tenant = get_tenant_from_token(self.request)
        user_id = self.request.auth.get('user_id') if hasattr(self.request, 'auth') else None
        serializer.save(tenant=tenant, created_by_id=user_id, created_by_type='TENANT_USER')
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm a booking"""
        booking = self.get_object()
        booking.status = 'CONFIRMED'
        booking.save()
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a booking"""
        booking = self.get_object()
        booking.status = 'CANCELLED'
        booking.save()
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def checkin(self, request, pk=None):
        """Check in a booking"""
        booking = self.get_object()
        booking.status = 'CHECKED_IN'
        booking.save()
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def checkout(self, request, pk=None):
        """Check out a booking"""
        booking = self.get_object()
        booking.status = 'CHECKED_OUT'
        booking.save()
        serializer = self.get_serializer(booking)
        return Response(serializer.data)


class BookingItemViewSet(viewsets.ModelViewSet):
    queryset = BookingItem.objects.all()
    serializer_class = BookingItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['booking']


class BookingGuestInfoViewSet(viewsets.ModelViewSet):
    queryset = BookingGuestInfo.objects.all()
    serializer_class = BookingGuestInfoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['booking', 'is_primary']


# ===== Payment ViewSets =====

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['booking', 'status', 'method']
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        tenant = get_tenant_from_token(self.request)
        if tenant:
            return Payment.objects.filter(booking__tenant=tenant)
        return Payment.objects.none()


# ===== Invoice & Payout ViewSets =====

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['booking']
    
    def get_queryset(self):
        tenant = get_tenant_from_token(self.request)
        if tenant:
            return Invoice.objects.filter(booking__tenant=tenant)
        return Invoice.objects.none()


class PayoutViewSet(viewsets.ModelViewSet):
    queryset = Payout.objects.all()
    serializer_class = PayoutSerializer
    permission_classes = [IsAuthenticated, IsTenantOwner]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['scheduled_at', 'processed_at']
    
    def get_queryset(self):
        tenant = get_tenant_from_token(self.request)
        if tenant:
            return Payout.objects.filter(tenant=tenant)
        return Payout.objects.none()
    
    def perform_create(self, serializer):
        tenant = get_tenant_from_token(self.request)
        serializer.save(tenant=tenant)


# ===== Webhook & Audit ViewSets =====

class WebhookRegistrationViewSet(viewsets.ModelViewSet):
    queryset = WebhookRegistration.objects.all()
    serializer_class = WebhookRegistrationSerializer
    permission_classes = [IsAuthenticated, IsTenantOwner]
    
    def get_queryset(self):
        tenant = get_tenant_from_token(self.request)
        if tenant:
            return WebhookRegistration.objects.filter(tenant=tenant)
        return WebhookRegistration.objects.none()
    
    def perform_create(self, serializer):
        tenant = get_tenant_from_token(self.request)
        serializer.save(tenant=tenant)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsTenantOwnerOrManager]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['actor', 'action']
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        tenant = get_tenant_from_token(self.request)
        if tenant:
            return AuditLog.objects.filter(tenant=tenant)
        return AuditLog.objects.none()
