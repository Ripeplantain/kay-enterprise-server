from datetime import datetime
from rest_framework import serializers
from .models import Payment
from booking.models import Booking
from decimal import Decimal
import uuid

class PaymentListSerializer(serializers.ModelSerializer):
    """Serializer for payment listings"""
    booking_reference = serializers.CharField(source='booking.booking_reference', read_only=True)
    passenger_name = serializers.CharField(source='booking.passenger_name', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_reference', 'booking_reference', 'passenger_name',
            'amount', 'currency', 'payment_method', 'status', 'created_at'
        ]

class PaymentDetailSerializer(serializers.ModelSerializer):
    """Detailed payment information"""
    booking_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_reference', 'booking_details', 'amount', 'currency',
            'payment_method', 'mobile_money_provider', 'mobile_money_number',
            'status', 'gateway_response', 'gateway_reference',
            'created_at', 'processed_at', 'notes'
        ]
        read_only_fields = ('id', 'payment_reference', 'created_at')

    def get_booking_details(self, obj):
        return {
            'booking_reference': obj.booking.booking_reference,
            'passenger_name': obj.booking.passenger_name,
            'route': obj.booking.trip.route.name,
            'total_amount': obj.booking.total_amount
        }

class PaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating payments"""
    
    class Meta:
        model = Payment
        fields = [
            'booking', 'payment_method', 'mobile_money_provider',
            'mobile_money_number'
        ]

    def validate_mobile_money_number(self, value):
        """Validate mobile money number for Ghana"""
        if value and not value.startswith(('+233', '0')):
            raise serializers.ValidationError("Enter a valid Ghanaian mobile money number")
        return value

    def validate(self, attrs):
        """Validate payment data"""
        payment_method = attrs.get('payment_method')
        
        # If mobile money, provider and number are required
        if payment_method == 'mobile_money':
            if not attrs.get('mobile_money_provider'):
                raise serializers.ValidationError("Mobile money provider is required")
            if not attrs.get('mobile_money_number'):
                raise serializers.ValidationError("Mobile money number is required")
        
        # Check if booking is payable
        booking = attrs.get('booking')
        if booking and booking.payment_status == 'paid':
            raise serializers.ValidationError("This booking has already been paid")
        
        return attrs

    def create(self, validated_data):
        """Create payment record"""
        booking = validated_data['booking']
        
        # Generate payment reference
        payment_reference = f"PAY{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
        
        # Create payment
        payment = Payment.objects.create(
            payment_reference=payment_reference,
            amount=booking.total_amount,
            currency='GHS',
            **validated_data
        )
        
        return payment