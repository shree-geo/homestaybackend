"""
Django models for GrihaStay application
Mapping from PostgreSQL schema to Django ORM
"""
import uuid
from django.contrib.gis.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone


# ===== Location Models =====

class Country(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    code = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'country'
        verbose_name_plural = 'Countries'

    def __str__(self):
        return self.name


class State(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='states')
    name = models.TextField()
    code = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'state'

    def __str__(self):
        return self.name


class District(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='districts')
    name = models.TextField()
    code = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'district'

    def __str__(self):
        return self.name


class Municipality(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='municipalities')
    name = models.TextField()
    code = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'municipality'
        verbose_name_plural = 'Municipalities'

    def __str__(self):
        return self.name


class City(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='cities')
    name = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'city'
        verbose_name_plural = 'Cities'

    def __str__(self):
        return self.name


# ===== Community Models =====

class Community(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    description = models.TextField(null=True, blank=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True)
    municipality = models.ForeignKey(Municipality, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'community'
        verbose_name_plural = 'Communities'
        unique_together = [['name', 'municipality']]

    def __str__(self):
        return self.name


class CommunityMedia(models.Model):
    MEDIA_TYPE_CHOICES = [
        ('IMAGE', 'Image'),
        ('VIDEO', 'Video'),
        ('DOCUMENT', 'Document'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='media')
    media_name = models.TextField()
    media_file_name = models.TextField()
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPE_CHOICES, default='IMAGE')
    media_status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'community_media'
        verbose_name_plural = 'Community Media'

    def __str__(self):
        return f"{self.media_name} ({self.community.name})"


# ===== Tenant & User Models =====

class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    contact_email = models.TextField(null=True, blank=True)
    contact_phone = models.TextField(null=True, blank=True)
    registration_number = models.TextField(null=True, blank=True)
    currency = models.CharField(max_length=8, default='NPR')
    timezone = models.TextField(default='Asia/Kathmandu')
    locale = models.TextField(default='en')
    plan = models.TextField(default='free')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tenants'

    def __str__(self):
        return self.name


class TenantUserManager(BaseUserManager):
    def create_user(self, user_name, email=None, password=None, **extra_fields):
        if not user_name:
            raise ValueError('The user_name field must be set')
        user = self.model(user_name=user_name, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, user_name, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'OWNER')
        return self.create_user(user_name, email, password, **extra_fields)


class TenantUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('OWNER', 'Owner'),
        ('MANAGER', 'Manager'),
        ('RECEPTIONIST', 'Receptionist'),
        ('HOUSEKEEPING', 'Housekeeping'),
        ('AUDITOR', 'Auditor'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='RECEPTIONIST')
    user_name = models.TextField(unique=True)
    email = models.TextField(null=True, blank=True)
    full_name = models.TextField(null=True, blank=True)
    mobile_number = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    mobile_verified = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    verification_token = models.TextField(null=True, blank=True)
    reset_password_token = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantUserManager()

    USERNAME_FIELD = 'user_name'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'tenant_users'
        unique_together = [['tenant', 'user_name']]

    def __str__(self):
        return f"{self.user_name} ({self.tenant.name if self.tenant else 'No Tenant'})"

    def update_last_login(self):
        self.last_login = timezone.now()
        self.save(update_fields=['last_login'])


class TenantApiKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='api_keys')
    key = models.TextField(unique=True)
    description = models.TextField(null=True, blank=True)
    scopes = models.JSONField(default=list)
    disabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tenant_api_keys'

    def __str__(self):
        return f"{self.tenant.name} - {self.description or 'API Key'}"


# ===== Property Type & Amenities =====

class PropertyType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(unique=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'property_types'

    def __str__(self):
        return self.name


class Amenity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'amenities'
        verbose_name_plural = 'Amenities'

    def __str__(self):
        return self.name


# ===== Property Models =====

class Property(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('LISTED', 'Listed'),
        ('UNLISTED', 'Unlisted'),
        ('SUSPENDED', 'Suspended'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='properties')
    property_type = models.ForeignKey(PropertyType, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.TextField()
    description = models.TextField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True)
    municipality = models.ForeignKey(Municipality, on_delete=models.SET_NULL, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    community = models.ForeignKey(Community, on_delete=models.SET_NULL, null=True, blank=True)
    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)
    geom = models.PointField(null=True, blank=True, srid=4326)
    timezone = models.TextField(default='Asia/Kathmandu')
    currency = models.CharField(max_length=8, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    amenities = models.ManyToManyField(Amenity, through='PropertyAmenity', related_name='properties')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'properties'
        verbose_name_plural = 'Properties'

    def __str__(self):
        return f"{self.name} ({self.tenant.name})"


class PropertyAmenity(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE)

    class Meta:
        db_table = 'property_amenities'
        unique_together = [['property', 'amenity']]


# ===== Room Models =====

class RoomType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='room_types')
    name = models.TextField()
    slug = models.TextField(null=True, blank=True)
    max_occupancy = models.IntegerField(default=2)
    default_base_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=8, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'room_types'

    def __str__(self):
        return f"{self.name} - {self.property.name}"


class Room(models.Model):
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('OCCUPIED', 'Occupied'),
        ('OUT_OF_SERVICE', 'Out of Service'),
        ('MAINTENANCE', 'Maintenance'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    price_override = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=8, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rooms'

    def __str__(self):
        return f"{self.room_number} - {self.room_type.name}"


class RoomImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    url = models.TextField()
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = 'room_images'


# ===== Rate Plans =====

class RatePlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='rate_plans')
    room_type = models.ForeignKey(RoomType, on_delete=models.SET_NULL, null=True, blank=True, related_name='rate_plans')
    name = models.TextField()
    description = models.TextField(null=True, blank=True)
    pricing_model = models.TextField(default='STATIC')
    currency = models.CharField(max_length=8, null=True, blank=True)
    base_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    min_stay = models.IntegerField(default=1)
    max_stay = models.IntegerField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rate_plans'

    def __str__(self):
        return f"{self.name} - {self.property.name}"


class RatePlanRule(models.Model):
    MODIFIER_TYPE_CHOICES = [
        ('AMOUNT', 'Amount'),
        ('PERCENT', 'Percent'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rate_plan = models.ForeignKey(RatePlan, on_delete=models.CASCADE, related_name='rules')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    days_of_week = models.JSONField(default=list, null=True, blank=True)
    min_occupancy = models.IntegerField(null=True, blank=True)
    max_occupancy = models.IntegerField(null=True, blank=True)
    modifier_type = models.CharField(max_length=20, choices=MODIFIER_TYPE_CHOICES, default='AMOUNT')
    modifier_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    priority = models.IntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'rate_plan_rules'


# ===== Inventory Models =====

class Inventory(models.Model):
    id = models.BigAutoField(primary_key=True)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='inventory')
    dt = models.DateField()
    available_count = models.IntegerField(default=0)
    blocked_count = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'inventory'
        unique_together = [['room_type', 'dt']]
        verbose_name_plural = 'Inventories'

    def __str__(self):
        return f"{self.room_type.name} - {self.dt}"


class ChannelAllocation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='channel_allocations')
    channel_code = models.TextField()
    allocated_count = models.IntegerField(default=0)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'channel_allocations'


class InventoryHold(models.Model):
    hold_token = models.TextField(primary_key=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    metadata = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'inventory_holds'


# ===== Guest Models =====

class Guest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    email = models.TextField(null=True, blank=True)
    phone = models.TextField(null=True, blank=True)
    nationality = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'guests'

    def __str__(self):
        return self.name


class TenantGuestProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='guest_profiles')
    guest = models.ForeignKey(Guest, on_delete=models.SET_NULL, null=True, blank=True)
    display_name = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tenant_guest_profiles'


# ===== Booking Models =====

class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('CHECKED_IN', 'Checked In'),
        ('CHECKED_OUT', 'Checked Out'),
        ('NO_SHOW', 'No Show'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    external_id = models.TextField(null=True, blank=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='bookings')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='bookings')
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='bookings')
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    source = models.TextField(default='MARKETPLACE')
    checkin = models.DateField()
    checkout = models.DateField()
    nights = models.IntegerField()
    guests_count = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=8, default='NPR')
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    hold_token = models.TextField(null=True, blank=True)
    created_by_type = models.TextField(default='VISITOR')
    created_by_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bookings'

    def __str__(self):
        return f"Booking {self.id} - {self.property.name}"


class BookingItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='items')
    code = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'booking_items'


class BookingGuestInfo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='guest_info')
    name = models.TextField()
    email = models.TextField(null=True, blank=True)
    phone = models.TextField(null=True, blank=True)
    nationality = models.TextField(null=True, blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = 'booking_guest_info'


# ===== Payment Models =====

class Payment(models.Model):
    METHOD_CHOICES = [
        ('GATEWAY', 'Gateway'),
        ('OFFLINE', 'Offline'),
        ('PAY_AT_PROPERTY', 'Pay at Property'),
        ('WALLET', 'Wallet'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    gateway = models.TextField(null=True, blank=True)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='GATEWAY')
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=8, default='NPR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    transaction_id = models.TextField(null=True, blank=True)
    raw_payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'


# ===== Invoice & Payout Models =====

class Invoice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='invoices')
    invoice_number = models.TextField(null=True, blank=True)
    pdf_url = models.TextField(null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'invoices'


class Payout(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=8, default='NPR')
    status = models.TextField(default='PENDING')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'payouts'


# ===== Webhook & Audit Models =====

class WebhookRegistration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='webhooks')
    url = models.TextField()
    events = models.JSONField()
    secret = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'webhook_registrations'


class IdempotencyKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.TextField(unique=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    endpoint = models.TextField(null=True, blank=True)
    request_hash = models.TextField(null=True, blank=True)
    response_payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'idempotency_keys'


class AuditLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='audit_logs')
    actor = models.TextField(null=True, blank=True)
    action = models.TextField(null=True, blank=True)
    details = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
