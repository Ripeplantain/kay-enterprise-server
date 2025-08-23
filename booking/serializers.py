from rest_framework import serializers
from .models import Route, Trip, Booking
from bus_management.models import Bus, BusTerminal
from bus_management.serializers import BusListSerializer, BusTerminalSerializer
from authentication.models import Client
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

class RouteListSerializer(serializers.ModelSerializer):
    """Serializer for route listings"""
    origin_city = serializers.CharField(source='origin_terminal.city_town', read_only=True)
    destination_city = serializers.CharField(source='destination_terminal.city_town', read_only=True)
    duration_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Route
        fields = [
            'id', 'name', 'origin_city', 'destination_city',
            'distance_km', 'estimated_duration_hours', 'duration_display',
            'fare', 'is_active'
        ]

    def get_duration_display(self, obj):
        """Human-readable duration"""
        hours = int(obj.estimated_duration_hours)
        minutes = int((obj.estimated_duration_hours - hours) * 60)
        return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"

class RouteDetailSerializer(serializers.ModelSerializer):
    """Detailed route information"""
    origin_terminal = BusTerminalSerializer(read_only=True)
    destination_terminal = BusTerminalSerializer(read_only=True)
    duration_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Route
        fields = [
            'id', 'name', 'origin_terminal', 'destination_terminal',
            'distance_km', 'estimated_duration_hours', 'duration_display',
            'fare', 'is_active', 'created_at'
        ]
        read_only_fields = ('id', 'created_at', 'duration_display')

    def get_duration_display(self, obj):
        hours = int(obj.estimated_duration_hours)
        minutes = int((obj.estimated_duration_hours - hours) * 60)
        return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"

class RouteCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating routes"""
    
    class Meta:
        model = Route
        fields = [
            'name', 'origin_terminal', 'destination_terminal',
            'distance_km', 'estimated_duration_hours', 'fare'
        ]

    def validate(self, attrs):
        """Validate route data"""
        if attrs.get('origin_terminal') == attrs.get('destination_terminal'):
            raise serializers.ValidationError("Origin and destination cannot be the same")
        
        if attrs.get('distance_km', 0) <= 0:
            raise serializers.ValidationError("Distance must be greater than 0")
        
        if attrs.get('estimated_duration_hours', 0) <= 0:
            raise serializers.ValidationError("Duration must be greater than 0")
        
        if attrs.get('fare', 0) <= 0:
            raise serializers.ValidationError("Fare must be greater than 0")
        
        return attrs

class TripListSerializer(serializers.ModelSerializer):
    """Serializer for trip listings"""
    bus_name = serializers.CharField(source='bus.name', read_only=True)
    bus_type = serializers.CharField(source='bus.bus_type', read_only=True)
    route_name = serializers.CharField(source='route.name', read_only=True)
    origin_city = serializers.CharField(source='route.origin_terminal.city_town', read_only=True)
    destination_city = serializers.CharField(source='route.destination_terminal.city_town', read_only=True)
    departure_date = serializers.SerializerMethodField()
    departure_time = serializers.SerializerMethodField()
    arrival_time = serializers.SerializerMethodField()
    
    class Meta:
        model = Trip
        fields = [
            'id', 'trip_number', 'bus_name', 'bus_type', 'route_name',
            'origin_city', 'destination_city', 'departure_date', 'departure_time',
            'arrival_time', 'available_seats', 'fare', 'status'
        ]

    def get_departure_date(self, obj):
        return obj.scheduled_departure.strftime('%Y-%m-%d')
    
    def get_departure_time(self, obj):
        return obj.scheduled_departure.strftime('%H:%M')
    
    def get_arrival_time(self, obj):
        return obj.scheduled_arrival.strftime('%H:%M')

class TripDetailSerializer(serializers.ModelSerializer):
    """Detailed trip information"""
    bus = BusListSerializer(read_only=True)
    route = RouteDetailSerializer(read_only=True)
    driver_name = serializers.CharField(source='driver.get_full_name', read_only=True)
    conductor_name = serializers.CharField(source='conductor.get_full_name', read_only=True)
    
    class Meta:
        model = Trip
        fields = [
            'id', 'trip_number', 'bus', 'route', 'driver_name', 'conductor_name',
            'scheduled_departure', 'scheduled_arrival', 'actual_departure',
            'actual_arrival', 'total_seats', 'available_seats', 'fare',
            'status', 'notes', 'created_at'
        ]
        read_only_fields = ('id', 'created_at')

class BookingListSerializer(serializers.ModelSerializer):
    """Serializer for booking listings"""
    trip_details = serializers.SerializerMethodField()
    route_name = serializers.CharField(source='trip.route.name', read_only=True)
    departure_date = serializers.DateTimeField(source='trip.scheduled_departure', read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'booking_reference', 'trip_details', 'route_name',
            'passenger_name', 'seat_numbers', 'number_of_seats',
            'total_amount', 'booking_status', 'payment_status',
            'departure_date', 'booking_date'
        ]

    def get_trip_details(self, obj):
        return f"{obj.trip.trip_number} - {obj.trip.bus.name}"

class BookingDetailSerializer(serializers.ModelSerializer):
    """Detailed booking information"""
    client_name = serializers.CharField(source='client.full_name', read_only=True)
    client_phone = serializers.CharField(source='client.phone_number', read_only=True)
    trip = TripDetailSerializer(read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'booking_reference', 'client_name', 'client_phone', 'trip',
            'passenger_name', 'passenger_phone', 'seat_numbers', 'number_of_seats',
            'fare_per_seat', 'total_fare', 'booking_fee', 'total_amount',
            'booking_status', 'payment_status', 'booking_date', 'payment_deadline',
            'check_in_time', 'special_requests', 'notes', 'created_at'
        ]
        read_only_fields = ('id', 'booking_reference', 'created_at')

class BookingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating bookings"""
    
    class Meta:
        model = Booking
        fields = [
            'trip', 'passenger_name', 'passenger_phone', 'seat_numbers',
            'number_of_seats', 'special_requests'
        ]

    def validate_passenger_phone(self, value):
        """Validate passenger phone number"""
        if not value.startswith(('+233', '0')):
            raise serializers.ValidationError("Enter a valid Ghanaian phone number")
        return value

    def validate_seat_numbers(self, value):
        """Validate seat numbers format"""
        if not value or not value.strip():
            raise serializers.ValidationError("Seat numbers are required")
        
        # Basic validation for seat format (e.g., "A1,A2" or "1,2,3")
        seats = [seat.strip() for seat in value.split(',')]
        if len(seats) == 0:
            raise serializers.ValidationError("At least one seat must be selected")
        
        return value

    def validate(self, attrs):
        """Validate booking data"""
        trip = attrs.get('trip')
        number_of_seats = attrs.get('number_of_seats', 1)
        seat_numbers = attrs.get('seat_numbers', '')
        
        # Check if trip exists and is bookable
        if not trip:
            raise serializers.ValidationError("Trip is required")
        
        if trip.status not in ['scheduled', 'boarding']:
            raise serializers.ValidationError("This trip is not available for booking")
        
        # Check seat availability
        if trip.available_seats < number_of_seats:
            raise serializers.ValidationError(
                f"Only {trip.available_seats} seats available on this trip"
            )
        
        # Validate seat count matches seat numbers
        seats_list = [seat.strip() for seat in seat_numbers.split(',') if seat.strip()]
        if len(seats_list) != number_of_seats:
            raise serializers.ValidationError(
                "Number of seats must match the count of seat numbers provided"
            )
        
        return attrs

    def create(self, validated_data):
        """Create booking with automatic calculations"""
        trip = validated_data['trip']
        number_of_seats = validated_data['number_of_seats']
        
        # Generate booking reference
        booking_reference = f"KB{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:6].upper()}"
        
        # Calculate pricing
        fare_per_seat = trip.fare
        total_fare = fare_per_seat * number_of_seats
        booking_fee = Decimal('2.00')
        total_amount = total_fare + booking_fee
        
        # Create booking
        booking = Booking.objects.create(
            booking_reference=booking_reference,
            client=self.context['request'].user,
            trip=trip,
            passenger_name=validated_data['passenger_name'],
            passenger_phone=validated_data['passenger_phone'],
            seat_numbers=validated_data['seat_numbers'],
            number_of_seats=number_of_seats,
            fare_per_seat=fare_per_seat,
            total_fare=total_fare,
            booking_fee=booking_fee,
            total_amount=total_amount,
            special_requests=validated_data.get('special_requests', ''),
            payment_deadline=datetime.now() + timedelta(hours=2)
        )
        
        # Update available seats
        trip.available_seats -= number_of_seats
        trip.save()
        
        return booking