from rest_framework import serializers
from .models import LuggageType, Luggage, LuggageTracking
from booking.models import Booking
from decimal import Decimal
import uuid

class LuggageTypeSerializer(serializers.ModelSerializer):
    """Serializer for luggage types"""
    dimensions_display = serializers.SerializerMethodField()
    price_display = serializers.SerializerMethodField()
    
    class Meta:
        model = LuggageType
        fields = [
            'id', 'name', 'description', 'max_weight_kg',
            'max_length_cm', 'max_width_cm', 'max_height_cm',
            'dimensions_display', 'base_price', 'price_per_kg',
            'price_display', 'is_active'
        ]
        read_only_fields = ('id', 'dimensions_display', 'price_display')

    def get_dimensions_display(self, obj):
        """Human-readable dimensions"""
        return f"{obj.max_length_cm}×{obj.max_width_cm}×{obj.max_height_cm}cm"
    
    def get_price_display(self, obj):
        """Human-readable pricing"""
        if obj.price_per_kg > 0:
            return f"GHS {obj.base_price} + GHS {obj.price_per_kg}/kg"
        return f"GHS {obj.base_price}"

class LuggageListSerializer(serializers.ModelSerializer):
    """Serializer for luggage listings"""
    booking_reference = serializers.CharField(source='booking.booking_reference', read_only=True)
    passenger_name = serializers.CharField(source='booking.passenger_name', read_only=True)
    luggage_type_name = serializers.CharField(source='luggage_type.name', read_only=True)
    
    class Meta:
        model = Luggage
        fields = [
            'id', 'luggage_tag', 'booking_reference', 'passenger_name',
            'luggage_type_name', 'description', 'weight_kg', 'status',
            'current_location', 'is_fragile', 'is_valuable',
            'registered_at'
        ]

class LuggageDetailSerializer(serializers.ModelSerializer):
    """Detailed luggage information"""
    booking_details = serializers.SerializerMethodField()
    luggage_type = LuggageTypeSerializer(read_only=True)
    dimensions_display = serializers.SerializerMethodField()
    handling_instructions = serializers.SerializerMethodField()
    tracking_history = serializers.SerializerMethodField()
    
    class Meta:
        model = Luggage
        fields = [
            'id', 'luggage_tag', 'booking_details', 'luggage_type',
            'description', 'weight_kg', 'dimensions_display',
            'is_fragile', 'fragile_level', 'is_valuable', 'declared_value',
            'handling_instructions', 'status', 'current_location',
            'luggage_fee', 'insurance_fee', 'photo_front', 'photo_side',
            'registered_at', 'loaded_at', 'arrived_at', 'collected_at',
            'collected_by', 'tracking_history'
        ]
        read_only_fields = ('id', 'luggage_tag', 'registered_at', 'tracking_history')

    def get_booking_details(self, obj):
        return {
            'booking_reference': obj.booking.booking_reference,
            'passenger_name': obj.booking.passenger_name,
            'route': obj.booking.trip.route.name,
            'departure_date': obj.booking.trip.scheduled_departure.date()
        }
    
    def get_dimensions_display(self, obj):
        return f"{obj.length_cm}×{obj.width_cm}×{obj.height_cm}cm"
    
    def get_handling_instructions(self, obj):
        instructions = []
        if obj.is_fragile:
            instructions.append(f"FRAGILE - {obj.get_fragile_level_display()}")
        if obj.requires_upright:
            instructions.append("Keep Upright")
        if obj.temperature_sensitive:
            instructions.append("Temperature Sensitive")
        if obj.special_instructions:
            instructions.append(obj.special_instructions)
        return instructions
    
    def get_tracking_history(self, obj):
        history = obj.tracking_history.all()[:10]  # Last 10 records
        return LuggageTrackingSerializer(history, many=True).data

class LuggageCreateSerializer(serializers.ModelSerializer):
    """Serializer for registering luggage"""
    
    class Meta:
        model = Luggage
        fields = [
            'booking', 'luggage_type', 'description', 'weight_kg',
            'length_cm', 'width_cm', 'height_cm', 'is_fragile',
            'fragile_level', 'is_valuable', 'declared_value',
            'special_instructions', 'requires_upright', 'temperature_sensitive',
            'photo_front', 'photo_side'
        ]

    def validate_weight_kg(self, value):
        """Validate luggage weight"""
        if value <= 0:
            raise serializers.ValidationError("Weight must be greater than 0")
        if value > 50:  # Maximum 50kg per item
            raise serializers.ValidationError("Maximum weight per item is 50kg")
        return value

    def validate(self, attrs):
        """Validate luggage against type limits"""
        luggage_type = attrs.get('luggage_type')
        weight_kg = attrs.get('weight_kg', 0)
        length_cm = attrs.get('length_cm', 0)
        width_cm = attrs.get('width_cm', 0)
        height_cm = attrs.get('height_cm', 0)
        
        if luggage_type:
            # Check weight limit
            if weight_kg > luggage_type.max_weight_kg:
                raise serializers.ValidationError(
                    f"Weight exceeds maximum for {luggage_type.name} ({luggage_type.max_weight_kg}kg)"
                )
            
            # Check dimension limits
            if (length_cm > luggage_type.max_length_cm or 
                width_cm > luggage_type.max_width_cm or 
                height_cm > luggage_type.max_height_cm):
                raise serializers.ValidationError(
                    f"Dimensions exceed limits for {luggage_type.name}"
                )
        
        # Validate fragile level if is_fragile is True
        if attrs.get('is_fragile') and attrs.get('fragile_level') == 'none':
            attrs['fragile_level'] = 'low'  # Default to low if fragile but no level set
        
        return attrs

    def create(self, validated_data):
        """Create luggage with automatic calculations"""
        luggage_type = validated_data['luggage_type']
        weight_kg = validated_data['weight_kg']
        
        # Generate luggage tag
        luggage_tag = f"LG{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:6].upper()}"
        
        # Calculate fees
        luggage_fee = luggage_type.base_price + (luggage_type.price_per_kg * weight_kg)
        insurance_fee = Decimal('0.00')
        
        if validated_data.get('is_valuable') and validated_data.get('declared_value', 0) > 0:
            # 1% of declared value as insurance fee
            insurance_fee = validated_data['declared_value'] * Decimal('0.01')
        
        # Create luggage
        luggage = Luggage.objects.create(
            luggage_tag=luggage_tag,
            luggage_fee=luggage_fee,
            insurance_fee=insurance_fee,
            current_location=validated_data['booking'].trip.route.origin_terminal.name,
            **validated_data
        )
        
        # Create initial tracking record
        LuggageTracking.objects.create(
            luggage=luggage,
            location=luggage.current_location,
            status="Registered",
            notes="Luggage registered and tagged",
            recorded_by=self.context.get('request').user if self.context.get('request') else None
        )
        
        return luggage

class LuggageUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating luggage status"""
    
    class Meta:
        model = Luggage
        fields = [
            'status', 'current_location', 'loaded_at', 'arrived_at',
            'collected_at', 'collected_by'
        ]

class LuggageTrackingSerializer(serializers.ModelSerializer):
    """Serializer for luggage tracking records"""
    recorded_by_name = serializers.CharField(source='recorded_by.get_full_name', read_only=True)
    
    class Meta:
        model = LuggageTracking
        fields = [
            'id', 'location', 'status', 'notes', 'recorded_by_name', 'timestamp'
        ]
        read_only_fields = ('id', 'timestamp', 'recorded_by_name')

class LuggageTrackingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating luggage tracking records"""
    
    class Meta:
        model = LuggageTracking
        fields = ['luggage', 'location', 'status', 'notes']

    def create(self, validated_data):
        """Create tracking record and update luggage"""
        tracking = LuggageTracking.objects.create(
            recorded_by=self.context.get('request').user if self.context.get('request') else None,
            **validated_data
        )
        
        # Update luggage current location and status
        luggage = validated_data['luggage']
        luggage.current_location = validated_data['location']
        luggage.status = validated_data['status'].lower()
        
        # Update timestamps based on status
        if validated_data['status'].lower() == 'loaded':
            luggage.loaded_at = tracking.timestamp
        elif validated_data['status'].lower() == 'arrived':
            luggage.arrived_at = tracking.timestamp
        elif validated_data['status'].lower() == 'collected':
            luggage.collected_at = tracking.timestamp
        
        luggage.save()
        
        return tracking
