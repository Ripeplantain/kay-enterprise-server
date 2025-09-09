from rest_framework import serializers
from .models import Agent
import re


class AgentRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = [
            'full_name', 'phone_number', 'email', 'id_type', 'id_number',
            'region', 'city_town', 'area_suburb', 'mobile_money_provider',
            'mobile_money_number', 'availability', 'referral_code', 'why_join'
        ]
        
    def validate_phone_number(self, value):
        ghana_phone_pattern = r'^(?:\+233|0)[2-9]\d{8}$'
        if not re.match(ghana_phone_pattern, value):
            raise serializers.ValidationError("Please enter a valid Ghana phone number")
        return value
    
    def validate_mobile_money_number(self, value):
        ghana_phone_pattern = r'^(?:\+233|0)[2-9]\d{8}$'
        if not re.match(ghana_phone_pattern, value):
            raise serializers.ValidationError("Please enter a valid Ghana phone number")
        return value
    
    def validate_id_number(self, value):
        if not re.match(r'^[a-zA-Z0-9]+$', value):
            raise serializers.ValidationError("ID number must be alphanumeric")
        return value
    
    def validate_region(self, value):
        valid_regions = [
            'Greater Accra', 'Ashanti', 'Western', 'Central', 'Volta',
            'Eastern', 'Northern', 'Upper East', 'Upper West', 'Brong Ahafo',
            'Western North', 'Ahafo', 'Bono', 'Bono East', 'Oti', 'Savannah',
            'North East'
        ]
        if value not in valid_regions:
            raise serializers.ValidationError("Please select a valid Ghana region")
        return value
    
    def validate_referral_code(self, value):
        if value:
            if not Agent.objects.filter(reference_number=value, status='approved').exists():
                raise serializers.ValidationError("Invalid referral code")
        return value
    
    def validate(self, attrs):
        if Agent.objects.filter(phone_number=attrs['phone_number']).exists():
            raise serializers.ValidationError({"phone_number": ["Phone number already registered"]})
        
        if Agent.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": ["Email already registered"]})
            
        return attrs


class AgentResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = ['id', 'reference_number', 'full_name', 'status', 'created_at']
        read_only_fields = ['id', 'reference_number', 'status', 'created_at']