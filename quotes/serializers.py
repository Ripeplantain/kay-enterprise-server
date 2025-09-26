from rest_framework import serializers
from .models import BusQuote
from datetime import date
import re


class BusQuoteRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusQuote
        fields = [
            'pickup_location', 'destination', 'travel_date', 'passengers',
            'trip_type', 'full_name', 'phone_number', 'email',
            'preferred_contact_method', 'additional_requirements'
        ]

    def validate_phone_number(self, value):
        ghana_pattern = r'^(0|\+233)[2-9][0-9]{8}$'
        if not re.match(ghana_pattern, value):
            raise serializers.ValidationError(
                "Please enter a valid Ghana phone number"
            )
        return value

    def validate_travel_date(self, value):
        if value < date.today():
            raise serializers.ValidationError(
                "Travel date cannot be in the past"
            )
        return value

    def validate_passengers(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "Number of passengers must be at least 1"
            )
        if value > 100:
            raise serializers.ValidationError(
                "Maximum 100 passengers allowed"
            )
        return value


class BusQuoteResponseSerializer(serializers.ModelSerializer):
    quote_id = serializers.IntegerField(source='id')

    class Meta:
        model = BusQuote
        fields = ['quote_id', 'reference_number']