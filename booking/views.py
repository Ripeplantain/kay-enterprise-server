from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters
from django.utils import timezone
from datetime import datetime

from bus_management.models import Bus
from .models import Route, Trip, Booking
from .serializers import (
    RouteListSerializer, RouteDetailSerializer, RouteCreateUpdateSerializer,
    TripListSerializer, TripDetailSerializer, BookingListSerializer,
    BookingDetailSerializer, BookingCreateSerializer
)

class RouteFilter(django_filters.FilterSet):
    """Filter for routes"""
    start_city = django_filters.CharFilter(
        field_name='origin_terminal__city_town', 
        lookup_expr='icontains'
    )
    end_city = django_filters.CharFilter(
        field_name='destination_terminal__city_town', 
        lookup_expr='icontains'
    )
    origin_region = django_filters.CharFilter(field_name='origin_terminal__region')
    destination_region = django_filters.CharFilter(field_name='destination_terminal__region')
    min_fare = django_filters.NumberFilter(field_name='fare', lookup_expr='gte')
    max_fare = django_filters.NumberFilter(field_name='fare', lookup_expr='lte')
    max_distance = django_filters.NumberFilter(field_name='distance_km', lookup_expr='lte')
    max_duration = django_filters.NumberFilter(field_name='estimated_duration_hours', lookup_expr='lte')
    
    class Meta:
        model = Route
        fields = ['is_active']

class RouteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing routes
    
    Permissions:
    - Read: Public access
    - Write: Authenticated users only
    
    Filtering:
    - start_city, end_city, regions, fare range, distance, duration
    """
    queryset = Route.objects.filter(is_active=True)
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchBackend, filters.OrderingFilter]
    filterset_class = RouteFilter
    search_fields = ['name', 'origin_terminal__city_town', 'destination_terminal__city_town']
    ordering_fields = ['name', 'distance_km', 'estimated_duration_hours', 'fare', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return RouteListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return RouteCreateUpdateSerializer
        return RouteDetailSerializer

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get popular routes based on booking count"""
        from django.db.models import Count
        
        popular_routes = Route.objects.filter(is_active=True).annotate(
            booking_count=Count('trips__bookings')
        ).order_by('-booking_count')[:10]
        
        serializer = RouteListSerializer(popular_routes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def available_trips(self, request, pk=None):
        """Get available trips for this route"""
        route = self.get_object()
        date_param = request.query_params.get('date')
        
        # Default to today if no date provided
        if date_param:
            try:
                trip_date = datetime.strptime(date_param, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    'error': 'Invalid date format. Use YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            trip_date = timezone.now().date()
        
        trips = Trip.objects.filter(
            route=route,
            scheduled_departure__date=trip_date,
            status__in=['scheduled', 'boarding'],
            available_seats__gt=0
        ).order_by('scheduled_departure')
        
        serializer = TripListSerializer(trips, many=True)
        return Response(serializer.data)

class TripFilter(django_filters.FilterSet):
    """Filter for trips"""
    route = django_filters.ModelChoiceFilter(queryset=Route.objects.all())
    bus = django_filters.ModelChoiceFilter(queryset=Bus.objects.all())
    status = django_filters.ChoiceFilter(choices=Trip.TRIP_STATUS)
    departure_date = django_filters.DateFilter(field_name='scheduled_departure__date')
    departure_date_from = django_filters.DateFilter(field_name='scheduled_departure__date', lookup_expr='gte')
    departure_date_to = django_filters.DateFilter(field_name='scheduled_departure__date', lookup_expr='lte')
    available_seats_min = django_filters.NumberFilter(field_name='available_seats', lookup_expr='gte')
    
    class Meta:
        model = Trip
        fields = ['route', 'bus', 'status']

class TripViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing trips
    
    Permissions:
    - Read: Public access
    - Write: Authenticated users only
    """
    queryset = Trip.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchBackend, filters.OrderingFilter]
    filterset_class = TripFilter
    search_fields = ['trip_number', 'route__name', 'bus__name']
    ordering_fields = ['scheduled_departure', 'scheduled_arrival', 'fare', 'available_seats']
    ordering = ['scheduled_departure']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return TripListSerializer
        return TripDetailSerializer

    def get_queryset(self):
        """Filter trips based on user permissions and availability"""
        queryset = Trip.objects.all()
        
        # For non-staff users, only show future trips that are bookable
        if not (self.request.user.is_authenticated and self.request.user.is_staff):
            queryset = queryset.filter(
                scheduled_departure__gt=timezone.now(),
                status__in=['scheduled', 'boarding']
            )
        
        return queryset

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def update_status(self, request, pk=None):
        """Update trip status"""
        trip = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Trip.TRIP_STATUS):
            return Response({
                'error': 'Invalid status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update timestamps based on status
        if new_status == 'departed' and not trip.actual_departure:
            trip.actual_departure = timezone.now()
        elif new_status == 'arrived' and not trip.actual_arrival:
            trip.actual_arrival = timezone.now()
        
        trip.status = new_status
        trip.save()
        
        return Response({
            'success': True,
            'message': f'Trip status updated to {new_status}'
        })

class BookingFilter(django_filters.FilterSet):
    """Filter for bookings"""
    bus = django_filters.ModelChoiceFilter(
        field_name='trip__bus',
        queryset=Bus.objects.all()
    )
    route = django_filters.ModelChoiceFilter(
        field_name='trip__route',
        queryset=Route.objects.all()
    )
    status = django_filters.ChoiceFilter(
        field_name='booking_status',
        choices=Booking.BOOKING_STATUS
    )
    payment_status = django_filters.ChoiceFilter(choices=Booking.PAYMENT_STATUS)
    departure_date = django_filters.DateFilter(field_name='trip__scheduled_departure__date')
    departure_date_from = django_filters.DateFilter(
        field_name='trip__scheduled_departure__date', 
        lookup_expr='gte'
    )
    departure_date_to = django_filters.DateFilter(
        field_name='trip__scheduled_departure__date', 
        lookup_expr='lte'
    )
    passenger_name = django_filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = Booking
        fields = ['booking_status', 'payment_status']

class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing bookings
    
    Permissions:
    - Read: Authenticated users only (own bookings + staff see all)
    - Write: Authenticated users only
    
    Filtering:
    - bus, route, status, payment_status, departure_date, passenger_name
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchBackend, filters.OrderingFilter]
    filterset_class = BookingFilter
    search_fields = ['booking_reference', 'passenger_name', 'passenger_phone']
    ordering_fields = ['booking_date', 'trip__scheduled_departure', 'total_amount']
    ordering = ['-booking_date']

    def get_queryset(self):
        """Filter bookings based on user permissions"""
        if self.request.user.is_staff:
            return Booking.objects.all()
        else:
            # Regular users only see their own bookings
            return Booking.objects.filter(client=self.request.user)

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return BookingListSerializer
        elif self.action == 'create':
            return BookingCreateSerializer
        return BookingDetailSerializer

    def perform_create(self, serializer):
        """Set the current user as the client for the booking"""
        serializer.save(client=self.request.user)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a booking"""
        booking = self.get_object()
        
        if booking.booking_status in ['cancelled', 'completed']:
            return Response({
                'error': 'Booking cannot be cancelled'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if trip hasn't departed
        if booking.trip.scheduled_departure <= timezone.now():
            return Response({
                'error': 'Cannot cancel booking for past trips'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update booking status
        booking.booking_status = 'cancelled'
        booking.save()
        
        # Return seats to trip availability
        booking.trip.available_seats += booking.number_of_seats
        booking.trip.save()
        
        return Response({
            'success': True,
            'message': 'Booking cancelled successfully'
        })

    @action(detail=True, methods=['post'])
    def check_in(self, request, pk=None):
        """Check in for a trip"""
        booking = self.get_object()
        
        if booking.booking_status != 'confirmed':
            return Response({
                'error': 'Booking must be confirmed to check in'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if booking.check_in_time:
            return Response({
                'error': 'Already checked in'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        booking.check_in_time = timezone.now()
        booking.save()
        
        return Response({
            'success': True,
            'message': 'Check-in successful'
        })
