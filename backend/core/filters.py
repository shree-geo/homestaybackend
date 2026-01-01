import django_filters
from django.db.models import OuterRef, Exists
from datetime import datetime

from .constants import ACTIVE_BOOKING_STATUSES
from .models import Property, Booking, Room


class PropertyAvailabilityFilter(django_filters.FilterSet):
    checkin = django_filters.DateFilter(method='filter_available_rooms')
    checkout = django_filters.DateFilter(method='filter_available_rooms')
    city_name = django_filters.CharFilter(field_name='city__name', lookup_expr='icontains')

    class Meta:
        model = Property
        fields = [
            'checkin',
            'checkout',
            'status',
            'property_type',
            'state',
            'district',
            'city',
            'community',
        ]

    def filter_available(self, queryset, name, value):
        if name == 'checkout':
            return queryset

        checkin = self.data.get('checkin')
        checkout = self.data.get('checkout')

        if not checkin or not checkout:
            return queryset

        try:
            checkin = datetime.strptime(checkin, "%Y-%m-%d").date()
            checkout = datetime.strptime(checkout, "%Y-%m-%d").date()
        except ValueError:
            return queryset.none()

        overlapping_booking = Booking.objects.filter(
            room=OuterRef('pk'),
            status__in=ACTIVE_BOOKING_STATUSES,
            checkin__lt=checkout,
            checkout__gt=checkin,
        )

        available_rooms = Room.objects.filter(
            room_type__property=OuterRef('pk'),
            status='AVAILABLE',
        ).annotate(
            has_overlap=Exists(overlapping_booking)
        ).filter(
            has_overlap=False
        )

        return queryset.annotate(
            has_available_room=Exists(available_rooms)
        ).filter(
            has_available_room=True
        )
