from .constants import ACTIVE_BOOKING_STATUSES
from .models import Booking

def has_overlapping_booking(room, checkin, checkout):
    overlaps = Booking.objects.filter(
        room=room,
        status__in=ACTIVE_BOOKING_STATUSES,
        checkin__lt=checkout,
        checkout__gt=checkin,
    )
    print("Overlapping bookings:", overlaps)
    return Booking.objects.filter(
        room=room,
        status__in=ACTIVE_BOOKING_STATUSES,
        checkin__lt=checkout,
        checkout__gt=checkin,
    ).exists()

