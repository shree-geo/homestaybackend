import django_filters
from django.db.models import Q
from datetime import datetime
from .models import Property, Booking


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

    def filter_available_rooms(self, queryset, name, value):
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

        overlapping_room_ids = Booking.objects.filter(
            Q(checkin__lt=checkout) & Q(checkout__gt=checkin),
            status__in=['PENDING', 'CONFIRMED', 'CHECKED_IN']
        ).values_list('room_id', flat=True)

        return queryset.filter(
            room_types__rooms__status='AVAILABLE'
        ).exclude(
            room_types__rooms__id__in=overlapping_room_ids
        ).distinct()

