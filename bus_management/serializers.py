from rest_framework import serializers
from .models import Bus, BusTerminal
from decimal import Decimal

class BusTerminalSerializer(serializers.ModelSerializer):
    """Serializer for bus terminals"""
    
    class Meta:
        model = BusTerminal
        fields = [
            'id', 'name', 'terminal_type', 'region', 'city_town', 
            'area_suburb', 'address', 'gps_coordinates',
            'has_waiting_area', 'has_restroom', 'has_food_court',
            'has_parking', 'has_luggage_storage', 'phone_number',
            'is_active', 'created_at'
        ]
        read_only_fields = ('id', 'created_at')

    def validate_phone_number(self, value):
        """Validate Ghanaian phone number format"""
        if value and not value.startswith(('+233', '0')):
            raise serializers.ValidationError("Enter a valid Ghanaian phone number")
        return value

class BusListSerializer(serializers.ModelSerializer):
    """Simplified serializer for bus listings"""
    
    class Meta:
        model = Bus
        fields = [
            'id', 'name', 'bus_number', 'bus_type', 'total_seats',
            'has_ac', 'has_wifi', 'has_entertainment', 'has_charging_ports',
            'status'
        ]

class BusDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for individual bus"""
    luggage_capacity_display = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()
    
    class Meta:
        model = Bus
        fields = [
            'id', 'name', 'registration_number', 'bus_number', 'bus_type',
            'make_model', 'year_manufactured', 'total_seats', 'available_seats',
            'has_ac', 'has_wifi', 'has_entertainment', 'has_charging_ports', 
            'has_restroom', 'luggage_compartment_capacity', 'max_luggage_weight',
            'luggage_capacity_display', 'features', 'status', 'bus_photo',
            'last_maintenance_date', 'next_maintenance_date', 'created_at'
        ]
        read_only_fields = ('id', 'created_at', 'luggage_capacity_display', 'features')

    def get_luggage_capacity_display(self, obj):
        """Human-readable luggage capacity"""
        return f"{obj.luggage_compartment_capacity}m³, Max {obj.max_luggage_weight}kg"
    
    def get_features(self, obj):
        """List of bus features"""
        features = []
        if obj.has_ac:
            features.append("Air Conditioning")
        if obj.has_wifi:
            features.append("Free WiFi")
        if obj.has_entertainment:
            features.append("Entertainment System")
        if obj.has_charging_ports:
            features.append("Charging Ports")
        if obj.has_restroom:
            features.append("Onboard Restroom")
        return features

class BusCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating buses"""
    
    class Meta:
        model = Bus
        fields = [
            'name', 'registration_number', 'bus_number', 'bus_type',
            'make_model', 'year_manufactured', 'total_seats',
            'has_ac', 'has_wifi', 'has_entertainment', 'has_charging_ports',
            'has_restroom', 'luggage_compartment_capacity', 'max_luggage_weight',
            'bus_photo', 'last_maintenance_date', 'next_maintenance_date'
        ]

    def validate_registration_number(self, value):
        """Validate Ghana registration number format"""
        if not value or len(value.strip()) < 6:
            raise serializers.ValidationError("Enter a valid Ghana registration number")
        return value.upper().strip()

    def validate_total_seats(self, value):
        """Validate seat count"""
        if value < 10 or value > 100:
            raise serializers.ValidationError("Bus must have between 10 and 100 seats")
        return value

    def validate_year_manufactured(self, value):
        """Validate manufacturing year"""
        from datetime import datetime
        current_year = datetime.now().year
        if value < 1990 or value > current_year + 1:
            raise serializers.ValidationError(f"Year must be between 1990 and {current_year + 1}")
        return value