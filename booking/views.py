from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from datetime import datetime
from authentication.authentication import ClientOrAdminPermission
from .models import Route, Bus, Seat, Trip, LuggageType, Booking
from .serializers import (
    RouteSerializer, BusSerializer, TripSerializer, TripListSerializer,
    LuggageTypeSerializer, BookingSerializer, CreateBookingSerializer
)


class RouteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Route.objects.filter(is_active=True)
    serializer_class = RouteSerializer
    permission_classes = [ClientOrAdminPermission]


class BusViewSet(viewsets.ModelViewSet):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer
    permission_classes = [ClientOrAdminPermission]

    def get_queryset(self):
        queryset = Bus.objects.all()

        # Filter by bus type
        bus_type = self.request.query_params.get('bus_type')
        if bus_type:
            queryset = queryset.filter(bus_type=bus_type)

        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset.order_by('plate_number')

    def perform_create(self, serializer):
        # Check if user is admin for create operations
        user = self.request.user
        if not (hasattr(user, 'is_staff') and user.is_staff):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only admin users can create buses")
        serializer.save()

    def perform_update(self, serializer):
        # Check if user is admin for update operations
        user = self.request.user
        if not (hasattr(user, 'is_staff') and user.is_staff):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only admin users can update buses")
        serializer.save()

    def perform_destroy(self, instance):
        # Check if user is admin for delete operations
        user = self.request.user
        if not (hasattr(user, 'is_staff') and user.is_staff):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only admin users can delete buses")
        instance.delete()


class TripViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TripListSerializer
    permission_classes = [ClientOrAdminPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['route', 'status']
    
    def get_queryset(self):
        queryset = Trip.objects.filter(status='scheduled').select_related('route', 'bus')
        
        # Filter by origin and destination
        origin = self.request.query_params.get('origin')
        destination = self.request.query_params.get('destination')
        departure_date = self.request.query_params.get('departure_date')
        
        if origin:
            queryset = queryset.filter(route__origin__icontains=origin)
        if destination:
            queryset = queryset.filter(route__destination__icontains=destination)
        if departure_date:
            try:
                date = datetime.strptime(departure_date, '%Y-%m-%d').date()
                queryset = queryset.filter(departure_datetime__date=date)
            except ValueError:
                pass
        
        return queryset.order_by('departure_datetime')
    
    def retrieve(self, request, *args, **kwargs):
        trip = self.get_object()
        serializer = TripSerializer(trip, context={'trip_id': trip.id})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def seats(self, request, pk=None):
        trip = self.get_object()
        bus_serializer = BusSerializer(trip.bus, context={'trip_id': trip.id})
        return Response(bus_serializer.data)


class LuggageTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LuggageType.objects.filter(is_active=True)
    serializer_class = LuggageTypeSerializer
    permission_classes = [ClientOrAdminPermission]


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [ClientOrAdminPermission]
    
    def get_queryset(self):
        user = self.request.user
        
        # If it's an admin (Django User), show all bookings
        if hasattr(user, 'is_staff') and user.is_staff:
            return Booking.objects.all().select_related(
                'trip', 'trip__route', 'trip__bus', 'seat', 'client'
            ).prefetch_related('luggage_items')
        
        # If it's a client, show only their bookings
        if hasattr(user, 'phone_number'):  # This is a Client object
            client = user
        else:  # This is a Django User object with client relationship
            client = user.client
        
        return Booking.objects.filter(
            client=client
        ).select_related('trip', 'trip__route', 'trip__bus', 'seat').prefetch_related('luggage_items')
    
    def create(self, request, *args, **kwargs):
        serializer = CreateBookingSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            bookings = serializer.save()  # Now returns list of bookings
            response_serializer = BookingSerializer(bookings, many=True)
            return Response({
                'success': True,
                'message': f'{len(bookings)} booking(s) created successfully',
                'bookings': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'message': 'Booking creation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        
        if booking.status not in ['pending', 'confirmed']:
            return Response(
                {'error': 'Cannot cancel this booking'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update booking status
        booking.status = 'cancelled'
        booking.save()
        
        # Update trip available seats
        trip = booking.trip
        trip.available_seats += 1
        trip.save()
        
        return Response({'message': 'Booking cancelled successfully'})


class SearchTripsView(viewsets.GenericViewSet):
    permission_classes = [ClientOrAdminPermission]
    serializer_class = TripListSerializer
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        origin = request.query_params.get('origin')
        destination = request.query_params.get('destination')
        departure_date = request.query_params.get('departure_date')
        
        if not all([origin, destination, departure_date]):
            return Response(
                {'error': 'origin, destination, and departure_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            date = datetime.strptime(departure_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        trips = Trip.objects.filter(
            route__origin__icontains=origin,
            route__destination__icontains=destination,
            departure_datetime__date=date,
            status='scheduled',
            available_seats__gt=0
        ).select_related('route', 'bus').order_by('departure_datetime')
        
        # Use pagination
        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(trips, request, view=self)
        if page is not None:
            serializer = TripListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = TripListSerializer(trips, many=True)
        return Response({
            'count': trips.count(),
            'next': None,
            'previous': None,
            'results': serializer.data
        })
