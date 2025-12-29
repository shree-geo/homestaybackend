"""
DRF ViewSets for GrihaStay application
"""
from uuid import UUID

from django.db import transaction
from django.http import request
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import *
from .serializers import *
from .permissions import *
from .utils import has_overlapping_booking


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
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'property_type', 'state', 'district', 'city', 'community']
    search_fields = ['name', 'description', 'address']
    ordering_fields = ['name', 'created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [BelongsToTenant()]

    def get_queryset(self):
        tenant = get_tenant_from_token(self.request)

        base_qs = Property.objects.select_related(
            'property_type',
            'state',
            'state__country',
            'district',
            'district__state',
            'municipality',
            'municipality__district',
            'city',
            'city__district',
            'community',
            'community__state',
            'community__district',
            'community__municipality'
        ).prefetch_related('amenities')

        if not tenant:
            return base_qs.filter(status='LISTED')

        return base_qs.filter(tenant=tenant)

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)


# ===== House Rules ViewSets =====
class HouseRuleViewSet(viewsets.ModelViewSet):
    """Master house rule definitions (global/reusable rules)"""
    queryset = HouseRule.objects.all()
    serializer_class = HouseRuleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description']


class PropertyHouseRuleViewSet(viewsets.ModelViewSet):
    """Property-specific house rule associations"""
    queryset = PropertyHouseRule.objects.all()
    serializer_class = PropertyHouseRuleSerializer
    permission_classes = [IsAuthenticated, BelongsToTenant]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['property', 'house_rule']
    ordering_fields = ['order']

    def get_queryset(self):
        """Only associations for properties owned by current tenant"""
        tenant = get_tenant_from_token(self.request)
        if tenant:
            return PropertyHouseRule.objects.filter(
                property__tenant=tenant
            ).select_related('house_rule', 'property').order_by('order')
        return PropertyHouseRule.objects.none()

    def perform_create(self, serializer):
        """Ensure property belongs to tenant before creating association"""
        property_obj = serializer.validated_data['property']
        tenant = get_tenant_from_token(self.request)
        
        if property_obj.tenant != tenant:
            return Response(
                {'error': 'Property not found or does not belong to your tenant'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        serializer.save()

    @action(detail=False, methods=['post'], url_path='bulk-create')
    def bulk_create(self, request):
        """Create multiple property-house-rule associations at once"""
        serializer = PropertyHouseRuleBulkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tenant = get_tenant_from_token(request)
        rules = serializer.validated_data['rules']

        # Verify all properties belong to tenant
        for rule in rules:
            property_obj = rule['property']
            if property_obj.tenant != tenant:
                return Response(
                    {'error': f'Property {property_obj.id} does not belong to your tenant'}, 
                    status=status.HTTP_403_FORBIDDEN
                )

        instances = serializer.save()
        return Response(
            PropertyHouseRuleSerializer(instances, many=True).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get'], url_path='by-property/(?P<property_id>[^/.]+)')
    def by_property(self, request, property_id=None):
        """Get all house rules for a specific property"""
        tenant = get_tenant_from_token(request)
        if not tenant:
            return Response([], status=status.HTTP_200_OK)
        
        # Verify property belongs to tenant
        try:
            property_obj = Property.objects.get(id=property_id, tenant=tenant)
        except Property.DoesNotExist:
            return Response(
                {'error': 'Property not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        rules = self.get_queryset().filter(property=property_obj)
        serializer = self.get_serializer(rules, many=True)
        return Response(serializer.data)


# ===== Room ViewSets =====

class RoomTypeViewSet(viewsets.ModelViewSet):
    queryset = RoomType.objects.all()
    serializer_class = RoomTypeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['property']
    search_fields = ['name', 'description']

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), BelongsToTenant()]

    def get_queryset(self):
        tenant = get_tenant_from_token(self.request)
        if tenant:
            return RoomType.objects.filter(property__tenant=tenant)
        return RoomType.objects.none()

    @action(detail=False, methods=['get'], url_path='by-property/(?P<property_id>[^/.]+)')
    def by_property(self, request, property_id=None):
        tenant = get_tenant_from_token(request)

        if not tenant:
            return Response([], status=status.HTTP_200_OK)

        try:
            Property.objects.get(id=property_id, tenant=tenant)
        except Property.DoesNotExist:
            return Response(
                {'error': 'Property not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        queryset = self.get_queryset().filter(property_id=property_id)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['room_type', 'status']
    search_fields = ['room_number']

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), BelongsToTenant()]

    def get_queryset(self):
        if self.request.method in permissions.SAFE_METHODS:
            return Room.objects.filter(status='AVAILABLE')

        tenant = get_tenant_from_token(self.request)
        if tenant:
            return Room.objects.filter(
                room_type__property__tenant=tenant
            )

        return Room.objects.none()

    @action(detail=False, methods=['get'], url_path='by-property/(?P<property_id>[^/.]+)')
    def by_property(self, request, property_id=None):
        tenant = get_tenant_from_token(request)

        queryset = Room.objects.filter(
            room_type__property_id=property_id
        ).select_related('room_type')

        if tenant:
            queryset = queryset.filter(
                room_type__property__tenant=tenant
            )
        else:
            queryset = queryset.filter(status='AVAILABLE')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), BelongsToTenant()]

    def get_queryset(self):
        tenant = get_tenant_from_token(self.request)
        if tenant:
            return Booking.objects.filter(tenant=tenant)
        return Booking.objects.none()

    @action(detail=True, methods=['post'])
    def checkin(self, request, pk=None):
        booking = self.get_object()
        booking.status = 'CHECKED_IN'
        booking.save(update_fields=['status'])
        if booking.room:
            booking.room.status = 'OCCUPIED'
            booking.room.save(update_fields=['status'])
        return Response(self.get_serializer(booking).data)

    @action(detail=True, methods=['post'])
    def checkout(self, request, pk=None):
        booking = self.get_object()
        booking.status = 'CHECKED_OUT'
        booking.save(update_fields=['status'])
        if booking.room:
            booking.room.status = 'AVAILABLE'
            booking.room.save(update_fields=['status'])
        return Response(self.get_serializer(booking).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        booking.status = 'CANCELLED'
        booking.save(update_fields=['status'])
        if booking.room:
            booking.room.status = 'AVAILABLE'
            booking.room.save(update_fields=['status'])
        return Response(self.get_serializer(booking).data)


class BookingItemViewSet(viewsets.ModelViewSet):
    queryset = BookingItem.objects.all()
    serializer_class = BookingItemSerializer
    permission_classes = [permissions.IsAuthenticated, BelongsToTenant]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['booking']


class BookingGuestInfoViewSet(viewsets.ModelViewSet):
    serializer_class = BookingGuestInfoSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        booking_id = self.request.query_params.get("booking")
        hold_token = self.request.query_params.get("hold_token")

        return BookingGuestInfo.objects.filter(
            booking_id=booking_id,
            booking__hold_token=hold_token
        )

    def perform_create(self, serializer):
        booking_id = self.request.data.get("booking")
        hold_token = self.request.data.get("hold_token")

        booking = Booking.objects.get(
            id=booking_id,
            hold_token=hold_token
        )

        serializer.save(booking=booking)

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


# ===== Media Cleanup ViewSet =====

class MediaCleanupViewSet(viewsets.ViewSet):
    """
    Media Cleanup Management (Super Admin Only)
    
    Provides endpoints to manage orphaned media files that were uploaded but never linked to any entity.
    All endpoints require Super Admin (is_superuser=True) authentication.
    """
    permission_classes = [IsSuperAdmin]
    
    @swagger_auto_schema(
        operation_summary="Get media storage statistics",
        operation_description="""
        Returns comprehensive statistics about media storage including:
        - Total media file count
        - Linked media count (files associated with entities)
        - Orphaned media count (files not linked to any entity)
        - Storage usage in MB
        - Orphaned storage percentage
        
        **Permission Required:** Super Admin
        """,
        responses={
            200: MediaStatisticsSerializer,
            403: "Forbidden - User is not a superuser"
        },
        tags=['Media Cleanup']
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get overall media storage statistics."""
        from config.utils.media_cleanup import get_media_statistics
        
        stats = get_media_statistics()
        serializer = MediaStatisticsSerializer(stats)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Identify orphaned media files",
        operation_description="""
        Identifies orphaned media files without deleting them.
        
        Orphaned files are those with:
        - content_type is NULL
        - object_id is NULL
        - created_at older than grace period
        
        Use this endpoint to preview what would be deleted before running actual cleanup.
        
        **Permission Required:** Super Admin
        """,
        request_body=MediaCleanupRequestSerializer,
        responses={
            200: openapi.Response(
                description="Orphaned files identified successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, example='success'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Found 150 orphaned media files'),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT, ref='#/definitions/OrphanedMediaIdentify'),
                    }
                )
            ),
            400: "Bad Request - Invalid parameters",
            403: "Forbidden - User is not a superuser"
        },
        tags=['Media Cleanup']
    )
    @action(detail=False, methods=['post'])
    def identify(self, request):
        """
        Identify orphaned media files without deleting them.
        
        Request body:
        {
            "grace_period_hours": 24  // Optional, default 24
        }
        
        Returns information about orphaned files including count, IDs,
        and total size.
        """
        from config.utils.media_cleanup import identify_orphaned_media
        
        request_serializer = MediaCleanupRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        
        grace_period = request_serializer.validated_data['grace_period_hours']
        
        result = identify_orphaned_media(grace_period_hours=grace_period)
        serializer = OrphanedMediaIdentifySerializer(result)
        
        return Response({
            'status': 'success',
            'message': f'Found {result["orphaned_count"]} orphaned media files',
            'data': serializer.data
        })
    
    @swagger_auto_schema(
        operation_summary="Clean up orphaned media files",
        operation_description="""
        Performs cleanup of orphaned media files from database and disk.
        
        **Parameters:**
        - `grace_period_hours`: Only delete files older than this (1-720 hours)
        - `dry_run`: If true, preview without deleting (default: false)
        - `batch_size`: Process files in batches (1-1000, default: 100)
        
        **Safety Features:**
        - Files within grace period are protected
        - Linked files (content_type not NULL) are never deleted
        - Batch processing prevents memory issues
        - All operations are logged to audit log
        
        **Dry Run Mode:**
        Always test with `dry_run: true` first to preview what will be deleted.
        
        **Permission Required:** Super Admin
        """,
        request_body=MediaCleanupRequestSerializer,
        responses={
            200: openapi.Response(
                description="Cleanup completed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, example='success'),
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING, 
                            example='Cleanup complete: Deleted 148 files, freed 305.2 MB'
                        ),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT, ref='#/definitions/MediaCleanupResponse'),
                    }
                ),
                examples={
                    'application/json': {
                        'status': 'success',
                        'message': 'Cleanup complete: Deleted 148 files, freed 305.2 MB',
                        'data': {
                            'dry_run': False,
                            'identified_count': 150,
                            'deleted_count': 148,
                            'failed_count': 2,
                            'total_size_freed_mb': 305.2,
                            'errors': []
                        }
                    }
                }
            ),
            400: "Bad Request - Invalid parameters",
            403: "Forbidden - User is not a superuser"
        },
        tags=['Media Cleanup']
    )
    @action(detail=False, methods=['post'])
    def cleanup(self, request):
        """
        Clean up orphaned media files.
        
        Request body:
        {
            "grace_period_hours": 24,  // Optional, default 24
            "dry_run": false,           // Optional, default false
            "batch_size": 100           // Optional, default 100
        }
        
        If dry_run is true, only identifies orphans without deleting.
        Returns cleanup results including deleted count and space freed.
        """
        from config.utils.media_cleanup import cleanup_orphaned_media
        
        request_serializer = MediaCleanupRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        
        grace_period = request_serializer.validated_data['grace_period_hours']
        dry_run = request_serializer.validated_data['dry_run']
        batch_size = request_serializer.validated_data['batch_size']
        
        result = cleanup_orphaned_media(
            grace_period_hours=grace_period,
            dry_run=dry_run,
            batch_size=batch_size
        )
        
        serializer = MediaCleanupResponseSerializer(result)
        
        status_message = (
            f'Dry run complete: Would delete {result["identified_count"]} files'
            if dry_run
            else f'Cleanup complete: Deleted {result["deleted_count"]} files, '
                 f'freed {result["total_size_freed_mb"]} MB'
        )
        
        # Log the cleanup action
        if not dry_run and result['deleted_count'] > 0:
            try:
                # Safely get username with fallback for users without user_name attribute
                username = getattr(request.user, 'user_name', 'unknown')
                AuditLog.objects.create(
                    tenant=None,  # System-level action
                    actor=f'superadmin:{username}',
                    action='media_cleanup',
                    details={
                        'deleted_count': result['deleted_count'],
                        'failed_count': result['failed_count'],
                        'size_freed_mb': result['total_size_freed_mb'],
                        'grace_period_hours': grace_period,
                    }
                )
            except Exception:
                # Don't fail cleanup if audit log fails
                pass
        
        return Response({
            'status': 'success',
            'message': status_message,
            'data': serializer.data
        })

