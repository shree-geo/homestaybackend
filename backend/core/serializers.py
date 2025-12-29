"""
DRF Serializers for GrihaStay application
"""
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.gis.geos import Point

from config.utils import mixins
from .models import *
from .utils import has_overlapping_booking


# ===== Location Serializers =====

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'


class StateSerializer(serializers.ModelSerializer):
    country_name = serializers.CharField(source='country.name', read_only=True)
    
    class Meta:
        model = State
        fields = '__all__'


class DistrictSerializer(serializers.ModelSerializer):
    state_name = serializers.CharField(source='state.name', read_only=True)
    
    class Meta:
        model = District
        fields = '__all__'


class MunicipalitySerializer(serializers.ModelSerializer):
    district_name = serializers.CharField(source='district.name', read_only=True)
    
    class Meta:
        model = Municipality
        fields = '__all__'


class CitySerializer(serializers.ModelSerializer):
    district_name = serializers.CharField(source='district.name', read_only=True)
    
    class Meta:
        model = City
        fields = '__all__'

class MultimediaSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    protected = serializers.BooleanField(default=True)

    class Meta:
        model = Multimedia
        fields = "__all__"

    def validate(self, data):
        if self.instance is None and not data.get("file"):
            raise serializers.ValidationError({
                "file": "File is required."
            })
        return data

    def create(self, validated_data):
        user = self.context["request"].user
        if user.is_authenticated:
            validated_data["created_by"] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "file" in validated_data and not validated_data["file"]:
            raise serializers.ValidationError({"file": "File cannot be empty."})
        return super().update(instance, validated_data)

# ===== Community Serializers =====


class CommunitySerializer(mixins.GenericMediaMixin,serializers.ModelSerializer):
    class Meta:
        model = Community
        fields = '__all__'
        media_fields = ["image"]

# ===== Tenant & User Serializers =====

class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class TenantUserSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    class Meta:
        model = TenantUser
        fields = ['id', 'tenant', 'tenant_name', 'role', 'user_name', 'email',
                  'full_name', 'mobile_number', 'is_active', 'email_verified', 
                  'mobile_verified', 'last_login', 'created_at', 'updated_at']
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at', 'last_login']


class TenantUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = TenantUser
        fields = ['user_name', 'email', 'password', 'full_name', 'mobile_number', 'role']
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = TenantUser(**validated_data)
        user.set_password(password)
        user.save()
        return user


class TenantRegistrationSerializer(serializers.Serializer):
    """Serializer for tenant registration with first admin user"""
    # Tenant information
    tenant_name = serializers.CharField(max_length=255)
    contact_email = serializers.EmailField(required=False, allow_blank=True)
    contact_phone = serializers.CharField(max_length=50, required=False, allow_blank=True)
    registration_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    currency = serializers.CharField(max_length=8, default='NPR')
    timezone = serializers.CharField(max_length=100, default='Asia/Kathmandu')
    
    # First user (admin) information
    user_name = serializers.CharField(max_length=255)
    # email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(max_length=255)
    mobile_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    
    def validate_user_name(self, value):
        if TenantUser.objects.filter(user_name=value).exists():
            raise serializers.ValidationError("User name already exists")
        return value
    
    def create(self, validated_data):
        # Create tenant
        tenant = Tenant.objects.create(
            name=validated_data['tenant_name'],
            contact_email=validated_data.get('contact_email', ''),
            contact_phone=validated_data.get('contact_phone', ''),
            registration_number=validated_data.get('registration_number', ''),
            currency=validated_data.get('currency', 'NPR'),
            timezone=validated_data.get('timezone', 'Asia/Kathmandu'),
        )
        
        # Create first user (admin/owner)
        user = TenantUser.objects.create_user(
            user_name=validated_data['user_name'],
            # email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data['full_name'],
            mobile_number=validated_data.get('mobile_number', ''),
            tenant=tenant,
            role='OWNER',
        )
        user.set_password(validated_data['password'])
        user.save()
        
        return {'tenant': tenant, 'user': user}


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'user_name'

    def validate(self, attrs):
        # Get username dynamically
        user_name = attrs.get(self.username_field)
        password = attrs.get('password')

        if not user_name or not password:
            raise serializers.ValidationError('Must include "user_name" and "password".')

        try:
            user = TenantUser.objects.get(user_name=user_name)
        except TenantUser.DoesNotExist:
            raise serializers.ValidationError('Invalid credentials')

        if not user.is_active:
            raise serializers.ValidationError('User account is disabled')

        if not user.check_password(password):
            raise serializers.ValidationError('Invalid credentials')

        # Update last login
        user.update_last_login()

        # Generate JWT
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        refresh['tenant_id'] = str(user.tenant.id)
        refresh['role'] = user.role
        refresh['user_name'] = user.user_name

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': TenantUserSerializer(user).data,
            'tenant': TenantSerializer(user.tenant).data,
        }

class TenantApiKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantApiKey
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


# ===== Property Serializers =====

class PropertyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyType
        fields = '__all__'


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = '__all__'


class PropertySerializer(mixins.GenericMediaMixin,serializers.ModelSerializer):
    amenities_list = AmenitySerializer(source='amenities', many=True, read_only=True)
    amenity_ids = serializers.PrimaryKeyRelatedField(
        source='amenities',
        many=True,
        queryset=Amenity.objects.all(),
        write_only=True,
        required=False
    )
    house_rule_ids = serializers.PrimaryKeyRelatedField(
        source='house_rules',
        many=True,
        queryset=HouseRule.objects.all(),
        write_only=True,
        required=False
    )

    property_type_name = serializers.CharField(source='property_type.name', read_only=True)
    state_detail = StateSerializer(source='state', read_only=True)
    district_detail = DistrictSerializer(source='district', read_only=True)
    municipality_detail = MunicipalitySerializer(source='municipality', read_only=True)
    city_detail = CitySerializer(source='city', read_only=True)
    community_detail = CommunitySerializer(source='community', read_only=True)
    house_rules_list = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Property
        fields = '__all__'
        media_fields = ["image","additional_images"]
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']

    def get_house_rules_list(self, obj):
        qs = PropertyHouseRule.objects.filter(property=obj).select_related('house_rule').order_by('order')
        return PropertyHouseRuleSerializer(qs, many=True).data

    def create(self, validated_data):
        amenities = validated_data.pop('amenities', [])
        house_rules = validated_data.pop('house_rules', [])

        instance = super().create(validated_data)

        if amenities:
            instance.amenities.set(amenities)

        if house_rules:
            instance.house_rules.set(house_rules)

        if instance.lat and instance.lon:
            instance.geom = Point(instance.lon, instance.lat)
            instance.save()

        return instance

    def update(self, instance, validated_data):
        amenities = validated_data.pop('amenities', None)
        house_rules = validated_data.pop('house_rules', None)

        instance = super().update(instance, validated_data)

        if amenities is not None:
            instance.amenities.set(amenities)

        if house_rules is not None:
            instance.house_rules.set(house_rules)

        if instance.lat and instance.lon:
            instance.geom = Point(instance.lon, instance.lat)
            instance.save()

        return instance


# ===== House Rules Serializers =====

class HouseRuleSerializer(serializers.ModelSerializer):
    """Serializer for master house rule definitions"""
    class Meta:
        model = HouseRule
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class PropertyHouseRuleSerializer(serializers.ModelSerializer):
    """Serializer for property-house rule associations"""
    house_rule_detail = HouseRuleSerializer(source='house_rule', read_only=True)
    property_name = serializers.CharField(source='property.name', read_only=True)
    
    class Meta:
        model = PropertyHouseRule
        fields = ['id', 'property', 'property_name', 'house_rule', 'house_rule_detail', 'order']
        read_only_fields = ['id']


class HouseRuleBulkCreateSerializer(serializers.Serializer):
    """Bulk create house rule master records"""
    rules = HouseRuleSerializer(many=True)

    def create(self, validated_data):
        rules_data = validated_data['rules']
        instances = [HouseRule(**data) for data in rules_data]
        return HouseRule.objects.bulk_create(instances)


class PropertyHouseRuleBulkCreateSerializer(serializers.Serializer):
    """Bulk create property-house rule associations"""
    rules = PropertyHouseRuleSerializer(many=True)

    def create(self, validated_data):
        rules_data = validated_data['rules']
        instances = [PropertyHouseRule(**data) for data in rules_data]
        return PropertyHouseRule.objects.bulk_create(instances)

# ===== Room Serializers =====

class RoomTypeSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(source='property.name', read_only=True)
    
    class Meta:
        model = RoomType
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class RoomSerializer(mixins.GenericMediaMixin, serializers.ModelSerializer):
    room_type_name = serializers.CharField(source='room_type.name', read_only=True)
    room_type_description = serializers.CharField( source='room_type.description', read_only=True)
    room_type_max_occupancy = serializers.IntegerField( source='room_type.max_occupancy', read_only=True )

    class Meta:
        model = Room
        fields = '__all__'
        media_fields = ["image"]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ===== Rate Plan Serializers =====

class RatePlanRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RatePlanRule
        fields = '__all__'


class RatePlanSerializer(serializers.ModelSerializer):
    rules = RatePlanRuleSerializer(many=True, read_only=True)
    property_name = serializers.CharField(source='property.name', read_only=True)
    
    class Meta:
        model = RatePlan
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


# ===== Inventory Serializers =====

class InventorySerializer(serializers.ModelSerializer):
    room_type_name = serializers.CharField(source='room_type.name', read_only=True)
    
    class Meta:
        model = Inventory
        fields = '__all__'
        read_only_fields = ['id', 'updated_at']


class ChannelAllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChannelAllocation
        fields = '__all__'


class InventoryHoldSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryHold
        fields = '__all__'


# ===== Guest Serializers =====

class GuestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guest
        fields = '__all__'


class TenantGuestProfileSerializer(serializers.ModelSerializer):
    guest_details = GuestSerializer(source='guest', read_only=True)
    
    class Meta:
        model = TenantGuestProfile
        fields = '__all__'
        read_only_fields = ['id', 'tenant']


# ===== Booking Serializers =====

class BookingItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingItem
        fields = '__all__'


class BookingGuestInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingGuestInfo
        fields = '__all__'


class BookingSerializer(serializers.ModelSerializer):
    guest_info = BookingGuestInfoSerializer(many=True, read_only=True)
    property_detail = PropertySerializer(source='property', read_only=True)
    guest_name = serializers.CharField(write_only=True)
    guest_email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    guest_phone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    guest_nationality = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'tenant', 'property', 'property_detail', 'room_type', 'room',
            'source', 'checkin', 'checkout', 'nights', 'guests_count',
            'status', 'payment_status', 'total_amount', 'currency',
            'guest_info',
            'guest_name', 'guest_email', 'guest_phone', 'guest_nationality',
        ]
        read_only_fields = ['id', 'tenant', 'nights', 'status', 'payment_status', 'property', 'room_type']

    def validate(self, data):
        checkin = data.get('checkin', getattr(self.instance, 'checkin', None))
        checkout = data.get('checkout', getattr(self.instance, 'checkout', None))

        if checkin and checkout and checkout <= checkin:
            raise serializers.ValidationError("Checkout must be after checkin")

        return data

    def create(self, validated_data):
        guest_name = validated_data.pop('guest_name')
        guest_email = validated_data.pop('guest_email', '')
        guest_phone = validated_data.pop('guest_phone', '')
        guest_nationality = validated_data.pop('guest_nationality', '')

        room = validated_data['room']

        if has_overlapping_booking(room, validated_data['checkin'], validated_data['checkout']):
            raise serializers.ValidationError({"detail": "Room is not available for selected dates"})

        room_type = room.room_type
        property_obj = room_type.property
        tenant = property_obj.tenant

        validated_data.update({
            'room_type': room_type,
            'property': property_obj,
            'tenant': tenant,
            'nights': (validated_data['checkout'] - validated_data['checkin']).days,
            'status': 'PENDING'
        })

        with transaction.atomic():
            booking = Booking.objects.create(**validated_data)

            BookingGuestInfo.objects.create(
                booking=booking,
                name=guest_name,
                email=guest_email,
                phone=guest_phone,
                nationality=guest_nationality,
                is_primary=True
            )

        return booking

    def update(self, instance, validated_data):
        validated_data.pop('checkin', None)
        validated_data.pop('checkout', None)
        return super().update(instance, validated_data)


class BookingCreateSerializer(serializers.Serializer):
    room = serializers.UUIDField(required=True)
    checkin = serializers.DateField()
    checkout = serializers.DateField()
    guests_count = serializers.IntegerField(default=1)
    source = serializers.CharField(default='MARKETPLACE')

    guest_name = serializers.CharField()
    guest_email = serializers.EmailField(required=False, allow_blank=True)
    guest_phone = serializers.CharField(required=False, allow_blank=True)
    guest_nationality = serializers.CharField(required=False, allow_blank=True)

    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField(default='NPR')

    def validate(self, data):
        if data['checkout'] <= data['checkin']:
            raise serializers.ValidationError("Checkout must be after checkin")
        return data


# ===== Payment Serializers =====

class PaymentSerializer(serializers.ModelSerializer):
    booking_id = serializers.UUIDField(source='booking.id', read_only=True)
    
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


# ===== Invoice & Payout Serializers =====

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'


class PayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payout
        fields = '__all__'
        read_only_fields = ['id', 'tenant']


# ===== Webhook & Audit Serializers =====

class WebhookRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookRegistration
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'created_at']


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


# ===== Media Cleanup Serializers =====

class MediaCleanupRequestSerializer(serializers.Serializer):
    """
    Serializer for media cleanup API requests.
    """
    grace_period_hours = serializers.IntegerField(
        default=24,
        min_value=1,
        max_value=720,
        help_text="Hours to wait before considering a file orphaned (default: 24)"
    )
    dry_run = serializers.BooleanField(
        default=False,
        help_text="If true, only preview what would be deleted without actually deleting"
    )
    batch_size = serializers.IntegerField(
        default=100,
        min_value=1,
        max_value=1000,
        help_text="Number of records to process in each batch (default: 100)"
    )


class MediaStatisticsSerializer(serializers.Serializer):
    """
    Serializer for media statistics response.
    """
    total_media_count = serializers.IntegerField()
    linked_media_count = serializers.IntegerField()
    orphaned_media_count = serializers.IntegerField()
    orphaned_percentage = serializers.FloatField()
    total_storage_mb = serializers.FloatField()
    orphaned_storage_mb = serializers.FloatField()
    media_root = serializers.CharField()


class OrphanedMediaIdentifySerializer(serializers.Serializer):
    """
    Serializer for orphaned media identification response.
    """
    orphaned_count = serializers.IntegerField()
    orphaned_ids = serializers.ListField(child=serializers.IntegerField())
    total_size_bytes = serializers.IntegerField()
    total_size_mb = serializers.FloatField()
    oldest_orphan = serializers.DateTimeField(allow_null=True)
    grace_period_hours = serializers.IntegerField()


class MediaCleanupResponseSerializer(serializers.Serializer):
    """
    Serializer for media cleanup response.
    """
    dry_run = serializers.BooleanField()
    identified_count = serializers.IntegerField()
    deleted_count = serializers.IntegerField()
    failed_count = serializers.IntegerField()
    total_size_freed_mb = serializers.FloatField()
    errors = serializers.ListField(child=serializers.CharField(), required=False)

