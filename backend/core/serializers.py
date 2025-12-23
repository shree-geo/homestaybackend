"""
DRF Serializers for GrihaStay application
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.gis.geos import Point
from .models import *


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


# ===== Community Serializers =====

class CommunityMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityMedia
        fields = '__all__'


class CommunitySerializer(serializers.ModelSerializer):
    media = CommunityMediaSerializer(many=True, read_only=True)
    
    class Meta:
        model = Community
        fields = '__all__'


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


class PropertySerializer(serializers.ModelSerializer):
    amenities_list = AmenitySerializer(source='amenities', many=True, read_only=True)
    amenity_ids = serializers.PrimaryKeyRelatedField(
        source='amenities',
        many=True,
        queryset=Amenity.objects.all(),
        write_only=True,
        required=False
    )
    property_type_name = serializers.CharField(source='property_type.name', read_only=True)
    
    class Meta:
        model = Property
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        amenities = validated_data.pop('amenities', [])
        property_obj = Property.objects.create(**validated_data)
        property_obj.amenities.set(amenities)
        
        # Set geom from lat/lon if provided
        if property_obj.lat and property_obj.lon:
            property_obj.geom = Point(property_obj.lon, property_obj.lat)
            property_obj.save()
        
        return property_obj
    
    def update(self, instance, validated_data):
        amenities = validated_data.pop('amenities', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update geom from lat/lon if changed
        if 'lat' in validated_data or 'lon' in validated_data:
            if instance.lat and instance.lon:
                instance.geom = Point(instance.lon, instance.lat)
        
        instance.save()
        
        if amenities is not None:
            instance.amenities.set(amenities)
        
        return instance


# ===== Room Serializers =====

class RoomImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomImage
        fields = '__all__'


class RoomTypeSerializer(serializers.ModelSerializer):
    images = RoomImageSerializer(many=True, read_only=True)
    property_name = serializers.CharField(source='property.name', read_only=True)
    
    class Meta:
        model = RoomType
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class RoomSerializer(serializers.ModelSerializer):
    room_type_name = serializers.CharField(source='room_type.name', read_only=True)
    
    class Meta:
        model = Room
        fields = '__all__'
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
    items = BookingItemSerializer(many=True, read_only=True)
    guest_info = BookingGuestInfoSerializer(many=True, read_only=True)
    property_name = serializers.CharField(source='property.name', read_only=True)
    room_type_name = serializers.CharField(source='room_type.name', read_only=True)
    
    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']
    
    def validate(self, data):
        if data.get('checkout') and data.get('checkin'):
            if data['checkout'] <= data['checkin']:
                raise serializers.ValidationError("Checkout date must be after checkin date")
            
            # Calculate nights
            delta = data['checkout'] - data['checkin']
            data['nights'] = delta.days
        
        return data


class BookingCreateSerializer(serializers.Serializer):
    """Serializer for creating a booking with guest info"""
    property_id = serializers.UUIDField()
    room_type_id = serializers.UUIDField()
    room_id = serializers.UUIDField(required=False, allow_null=True)
    checkin = serializers.DateField()
    checkout = serializers.DateField()
    guests_count = serializers.IntegerField(default=1)
    source = serializers.CharField(default='MARKETPLACE')
    
    # Guest information
    guest_name = serializers.CharField()
    guest_email = serializers.EmailField(required=False, allow_blank=True)
    guest_phone = serializers.CharField(required=False, allow_blank=True)
    guest_nationality = serializers.CharField(required=False, allow_blank=True)
    
    # Payment information
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
