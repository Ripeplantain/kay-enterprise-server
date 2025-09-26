import json
from rest_framework import serializers
from .models import Route, Bus, Seat, Trip, LuggageType, Booking, BookingLuggage


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = '__all__'


class SeatSerializer(serializers.ModelSerializer):
    is_booked = serializers.SerializerMethodField()
    
    class Meta:
        model = Seat
        fields = ['id', 'seat_number', 'seat_type', 'is_available', 'is_booked']
    
    def get_is_booked(self, obj):
        trip_id = self.context.get('trip_id')
        if trip_id:
            return Booking.objects.filter(
                trip_id=trip_id,
                seat=obj,
                status__in=['confirmed', 'pending']
            ).exists()
        return False


class BusSerializer(serializers.ModelSerializer):
    bus_id = serializers.IntegerField(source='id', read_only=True)
    seats = serializers.SerializerMethodField()

    class Meta:
        model = Bus
        fields = ['id', 'bus_id', 'plate_number', 'bus_type', 'total_seats', 'seats']
    
    def get_seats(self, obj):
        trip_id = self.context.get('trip_id')
        return SeatSerializer(
            obj.seats.all(),
            many=True,
            context={'trip_id': trip_id}
        ).data


class TripSerializer(serializers.ModelSerializer):
    route = RouteSerializer(read_only=True)
    bus = BusSerializer(read_only=True)
    
    class Meta:
        model = Trip
        fields = '__all__'


class TripListSerializer(serializers.ModelSerializer):
    route_name = serializers.CharField(source='route.name', read_only=True)
    origin = serializers.CharField(source='route.origin', read_only=True)
    destination = serializers.CharField(source='route.destination', read_only=True)
    bus_plate = serializers.CharField(source='bus.plate_number', read_only=True)
    bus_type = serializers.CharField(source='bus.bus_type', read_only=True)
    
    class Meta:
        model = Trip
        fields = [
            'id', 'route_name', 'origin', 'destination', 'bus_plate', 'bus_type',
            'departure_datetime', 'arrival_datetime', 'price_per_seat',
            'available_seats', 'status', 'pickup_points', 'drop_points'
        ]


class LuggageTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LuggageType
        fields = '__all__'


class BookingLuggageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingLuggage
        fields = [
            'id', 'has_luggage', 'luggage_count', 'special_items',
            'luggage_handling_fee', 'cargo_van_fee', 'special_items_fee',
            'total_luggage_fee', 'luggage_notes'
        ]


class BookingSerializer(serializers.ModelSerializer):
    luggage_items = BookingLuggageSerializer(many=True, required=False)
    trip_details = TripListSerializer(source='trip', read_only=True)
    seat_number = serializers.CharField(source='seat.seat_number', read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'booking_reference', 'trip', 'trip_details', 'seat', 'seat_number',
            'pickup_point_id', 'drop_point_id', 'total_amount', 'status',
            'luggage_items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['booking_reference', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        luggage_items_data = validated_data.pop('luggage_items', [])
        
        # Generate booking reference
        import uuid
        booking_reference = f"BK{uuid.uuid4().hex[:8].upper()}"
        validated_data['booking_reference'] = booking_reference
        
        # Add client from request context
        user = self.context['request'].user
        if hasattr(user, 'phone_number'):  # This is a Client object
            validated_data['client'] = user
        else:  # This is a Django User object
            validated_data['client'] = user.client
        
        booking = Booking.objects.create(**validated_data)
        
        # Create luggage items
        for luggage_data in luggage_items_data:
            BookingLuggage.objects.create(booking=booking, **luggage_data)
        
        # Update seat availability and trip available seats
        seat = validated_data['seat']
        trip = validated_data['trip']
        
        # Mark seat as unavailable for this trip (we'll handle this in views)
        if trip.available_seats > 0:
            trip.available_seats -= 1
            trip.save()
        
        return booking


class CreateBookingSerializer(serializers.Serializer):
    trip_id = serializers.IntegerField()
    seat_ids = serializers.ListField(child=serializers.IntegerField())  # Multiple seats
    pickup_point_id = serializers.CharField()
    drop_off_point_id = serializers.CharField()
    bus_id = serializers.IntegerField()
    luggage_info = serializers.JSONField(required=False)  # Store luggage information as JSON
    
    def validate(self, data):
        # Validate trip exists and is available
        try:
            trip = Trip.objects.get(id=data['trip_id'], status='scheduled')
        except Trip.DoesNotExist:
            raise serializers.ValidationError("Trip not found or not available")
        
        # Validate bus matches trip
        if trip.bus.id != data['bus_id']:
            raise serializers.ValidationError("Bus does not match the trip")
        
        # Validate all seats exist and are available for this trip
        seats = []
        for seat_id in data['seat_ids']:
            try:
                seat = Seat.objects.get(id=seat_id, bus=trip.bus)
            except Seat.DoesNotExist:
                raise serializers.ValidationError(f"Seat {seat_id} not found or not available for this trip")
            
            # Check if seat is already booked for this trip
            if Booking.objects.filter(
                trip=trip,
                seat=seat,
                status__in=['confirmed', 'pending']
            ).exists():
                raise serializers.ValidationError(f"Seat {seat_id} is already booked for this trip")
            
            seats.append(seat)
        
        data['trip'] = trip
        data['seats'] = seats
        
        return data
    
    def create(self, validated_data):
        trip = validated_data.pop('trip')
        seats = validated_data.pop('seats')
        luggage_info = validated_data.pop('luggage_info', {})
        
        # Get client from request
        user = self.context['request'].user
        if hasattr(user, 'phone_number'):  # This is a Client object
            client = user
        else:  # This is a Django User object
            client = user.client
        
        bookings = []
        
        # Create a booking for each seat
        for seat in seats:
            # Calculate total amount per seat
            seat_cost = trip.price_per_seat
            luggage_cost = luggage_info.get('total_luggage_fee', 0)
            total_amount = seat_cost + luggage_cost
            
            # Generate booking reference
            import uuid
            booking_reference = f"BK{uuid.uuid4().hex[:8].upper()}"
            
            booking = Booking.objects.create(
                booking_reference=booking_reference,
                client=client,
                trip=trip,
                seat=seat,
                pickup_point_id=validated_data['pickup_point_id'],
                drop_point_id=validated_data['drop_off_point_id'],
                total_amount=total_amount,
                status='confirmed'
            )
            
            # Create luggage info if provided
            if luggage_info:
                BookingLuggage.objects.create(
                    booking=booking,
                    has_luggage=luggage_info.get('has_luggage', False),
                    luggage_count=luggage_info.get('luggage_count', 0),
                    special_items=luggage_info.get('special_items', []),
                    luggage_handling_fee=luggage_info.get('luggage_handling_fee', 0),
                    cargo_van_fee=luggage_info.get('cargo_van_fee', 0),
                    special_items_fee=luggage_info.get('special_items_fee', 0),
                    total_luggage_fee=luggage_info.get('total_luggage_fee', 0)
                )
            
            bookings.append(booking)
        
        # Update trip available seats
        seats_count = len(seats)
        if trip.available_seats >= seats_count:
            trip.available_seats -= seats_count
            trip.save()
        
        return bookings