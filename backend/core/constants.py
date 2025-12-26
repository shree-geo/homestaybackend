# python
# File: backend/core/constants.py

MEDIA_TYPE_CHOICES = (
    ('IMAGE', 'Image'),
    ('VIDEO', 'Video'),
    ('DOCUMENT', 'Document'),
)

ROLE_CHOICES = (
    ('OWNER', 'Owner'),
    ('MANAGER', 'Manager'),
    ('RECEPTIONIST', 'Receptionist'),
    ('HOUSEKEEPING', 'Housekeeping'),
    ('AUDITOR', 'Auditor'),
)

PROPERTY_STATUS_CHOICES = (
    ('DRAFT', 'Draft'),
    ('LISTED', 'Listed'),
    ('UNLISTED', 'Unlisted'),
    ('SUSPENDED', 'Suspended'),
)

ROOM_STATUS_CHOICES = (
    ('AVAILABLE', 'Available'),
    ('OCCUPIED', 'Occupied'),
    ('OUT_OF_SERVICE', 'Out of Service'),
    ('MAINTENANCE', 'Maintenance'),
)

MODIFIER_TYPE_CHOICES = (
    ('AMOUNT', 'Amount'),
    ('PERCENT', 'Percent'),
)

BOOKING_STATUS_CHOICES = (
    ('PENDING', 'Pending'),
    ('CONFIRMED', 'Confirmed'),
    ('CANCELLED', 'Cancelled'),
    ('CHECKED_IN', 'Checked In'),
    ('CHECKED_OUT', 'Checked Out'),
    ('NO_SHOW', 'No Show'),
)

PAYMENT_STATUS_CHOICES = (
    ('PENDING', 'Pending'),
    ('PAID', 'Paid'),
    ('FAILED', 'Failed'),
    ('REFUNDED', 'Refunded'),
)

PAYMENT_METHOD_CHOICES = (
    ('GATEWAY', 'Gateway'),
    ('OFFLINE', 'Offline'),
    ('PAY_AT_PROPERTY', 'Pay at Property'),
    ('WALLET', 'Wallet'),
)

DEFAULT_TIMEZONE = 'Asia/Kathmandu'
DEFAULT_CURRENCY = 'NPR'
PRICING_MODEL_STATIC = 'STATIC'

__all__ = [
    'MEDIA_TYPE_CHOICES',
    'ROLE_CHOICES',
    'PROPERTY_STATUS_CHOICES',
    'ROOM_STATUS_CHOICES',
    'MODIFIER_TYPE_CHOICES',
    'BOOKING_STATUS_CHOICES',
    'PAYMENT_STATUS_CHOICES',
    'PAYMENT_METHOD_CHOICES',
    'DEFAULT_TIMEZONE',
    'DEFAULT_CURRENCY',
    'PRICING_MODEL_STATIC',
]

ACTIVE_BOOKING_STATUSES = [
    "PENDING",
    "CONFIRMED",
    "CHECKED_IN",
]