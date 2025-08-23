from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password, check_password

from utils.enums.auth import AuthMessage
from .models import Client

class AdminLoginSerializer(serializers.Serializer):
    """Admin login using Django User model"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if not username or not password:
            raise serializers.ValidationError(AuthMessage.ADMIN_CREDENTIALS_NOT_PROVIDED.value)
            
        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError(AuthMessage.ERROR_ADMIN_INVALID_CREDENTIALS.value)
        if not user.is_staff:
            raise serializers.ValidationError(AuthMessage.ADMIN_ACCESS_REQUIRED.value)
        if not user.is_active:
            raise serializers.ValidationError(AuthMessage.DISABLED_ACCOUNT.value)
        
        attrs['user'] = user
        return attrs

class ClientRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = Client
        fields = [
            'phone_number', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'other_names', 'date_of_birth', 'gender',
            'region', 'city_town', 'area_suburb',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
            'sms_notifications', 'email_notifications', 'whatsapp_notifications'
        ]

    def validate_phone_number(self, value):
        """Validate and normalize phone number"""
        # Normalize to +233 format
        if value.startswith('0'):
            value = '+233' + value[1:]
        elif not value.startswith('+233'):
            value = '+233' + value
        
        # Check if phone already exists
        if Client.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError(AuthMessage.PHONE_ALREADY_EXISTS.value)
        
        return value

    def validate_email(self, value):
        """Validate email uniqueness"""
        if value and Client.objects.filter(email=value).exists():
            raise serializers.ValidationError(AuthMessage.EMAIL_ALREADY_EXISTS.value)
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(AuthMessage.PASSWORD_MISMATCH.value)
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        validated_data['password_hash'] = make_password(password)
        return Client.objects.create(**validated_data)

class ClientLoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate_phone_number(self, value):
        """Normalize phone number"""
        if value.startswith('0'):
            value = '+233' + value[1:]
        elif not value.startswith('+233'):
            value = '+233' + value
        return value

    def validate(self, attrs):
        phone_number = attrs.get('phone_number')
        password = attrs.get('password')

        if not phone_number or not password:
            raise serializers.ValidationError(AuthMessage.CREDENTIALS_NOT_PROVIDED.value)
            
        try:
            client = Client.objects.get(phone_number=phone_number)
            if not client.is_active:
                raise serializers.ValidationError(AuthMessage.DISABLED_ACCOUNT.value)
            if not check_password(password, client.password_hash):
                raise serializers.ValidationError(AuthMessage.ERROR_INVALID_CREDENTIALS.value)
            attrs['client'] = client
            return attrs
        except Client.DoesNotExist:
            raise serializers.ValidationError(AuthMessage.ERROR_INVALID_CREDENTIALS.value)

class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')
        read_only_fields = ('id', 'date_joined')

class ClientSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    masked_phone = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            'id', 'phone_number', 'masked_phone', 'email', 'full_name',
            'first_name', 'last_name', 'other_names', 'date_of_birth', 'gender',
            'region', 'city_town', 'area_suburb',
            'is_verified', 'phone_verified_at',
            'date_joined', 'profile_picture'
        ]
        read_only_fields = ('id', 'date_joined', 'phone_verified_at')

    def get_masked_phone(self, obj):
        return obj.get_masked_phone()

class ClientUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            'email', 'first_name', 'last_name', 'other_names',
            'area_suburb',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
            'sms_notifications', 'email_notifications', 'whatsapp_notifications',
            'profile_picture'
        ]
