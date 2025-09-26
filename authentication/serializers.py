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
            'area_suburb',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
            'sms_notifications', 'email_notifications', 'whatsapp_notifications'
        ]

    def validate_phone_number(self, value):
        """Validate and normalize phone number"""
        import re
        
        # Remove all non-digit characters except + at the start
        clean_value = re.sub(r'[^\d+]', '', value)
        
        # Normalize to +233 format
        if clean_value.startswith('0'):
            normalized_value = '+233' + clean_value[1:]
        elif clean_value.startswith('233'):
            normalized_value = '+' + clean_value
        elif clean_value.startswith('+233'):
            normalized_value = clean_value
        else:
            # Assume it's a local number without country code
            normalized_value = '+233' + clean_value
        
        # Validate the format matches Ghana phone number pattern
        ghana_pattern = r'^\+233(20|23|24|26|27|28|50|53|54|55|56|57|59)\d{7}$'
        if not re.match(ghana_pattern, normalized_value):
            raise serializers.ValidationError("Enter a valid Ghanaian phone number (e.g., +233201234567 or 0201234567)")
        
        # Check if phone already exists
        if Client.objects.filter(phone_number=normalized_value).exists():
            raise serializers.ValidationError(AuthMessage.PHONE_ALREADY_EXISTS.value)
        
        return normalized_value

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
        import re
        
        # Remove all non-digit characters except + at the start
        clean_value = re.sub(r'[^\d+]', '', value)
        
        # Normalize to +233 format
        if clean_value.startswith('0'):
            normalized_value = '+233' + clean_value[1:]
        elif clean_value.startswith('233'):
            normalized_value = '+' + clean_value
        elif clean_value.startswith('+233'):
            normalized_value = clean_value
        else:
            # Assume it's a local number without country code
            normalized_value = '+233' + clean_value
        
        return normalized_value

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
            'area_suburb',
            'is_verified', 'phone_verified_at',
            'date_joined'
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
        ]

class ClientListSerializer(serializers.ModelSerializer):
    """Serializer for admin client list with booking counts"""
    full_name = serializers.ReadOnlyField()
    masked_phone = serializers.SerializerMethodField()
    booking_count = serializers.IntegerField(read_only=True)
    total_bookings_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    last_booking_date = serializers.DateTimeField(read_only=True)
    class Meta:
        model = Client
        fields = [
            'id', 'phone_number', 'masked_phone', 'email', 'full_name',
            'first_name', 'last_name', 'gender', 'is_active', 'is_verified', 'date_joined', 'last_login',
            'booking_count', 'total_bookings_amount', 'last_booking_date'
        ]
        read_only_fields = ('id', 'date_joined', 'last_login')

    def get_masked_phone(self, obj):
        return obj.get_masked_phone()
    

class ClientDetailSerializer(serializers.ModelSerializer):
    """Detailed client serializer for admin with full activity information"""
    full_name = serializers.ReadOnlyField()
    masked_phone = serializers.SerializerMethodField()
    
    # Activity statistics
    booking_count = serializers.IntegerField(read_only=True)
    total_bookings_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_paid_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    last_booking_date = serializers.DateTimeField(read_only=True)
    first_booking_date = serializers.DateTimeField(read_only=True)
    
    # Recent activity
    recent_bookings = serializers.SerializerMethodField()
    payment_history = serializers.SerializerMethodField()
    account_activity = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            # Basic info
            'id', 'phone_number', 'masked_phone', 'email', 'full_name',
            'first_name', 'last_name', 'other_names', 'date_of_birth', 'gender',
            
            # Location
            'area_suburb',
            
            # Emergency contact
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
            
            # Account status
            'is_active', 'is_verified', 'phone_verified_at', 'email_verified_at',
            'date_joined', 'last_login',
            
            # Preferences
            'sms_notifications', 'email_notifications', 'whatsapp_notifications',
            
            # Activity stats
            'booking_count', 'total_bookings_amount', 'total_paid_amount',
            'last_booking_date', 'first_booking_date',
            
            # Activity details
            'recent_bookings', 'payment_history', 'account_activity',
            
            # Timestamps
            'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'date_joined', 'created_at', 'updated_at')

    def get_masked_phone(self, obj):
        return obj.get_masked_phone()
    
    
    def get_recent_bookings(self, obj):
        """Get last 10 bookings with basic details"""
        from booking.serializers import BookingListSerializer
        recent_bookings = obj.bookings.select_related('trip__route', 'trip__bus').order_by('-booking_date')[:10]
        return BookingListSerializer(recent_bookings, many=True).data
    
    def get_payment_history(self, obj):
        """Get payment history for this client"""
        from payments.models import Payment
        from payments.serializers import PaymentListSerializer
        
        payments = Payment.objects.filter(
            booking__client=obj
        ).select_related('booking').order_by('-created_at')[:10]
        return PaymentListSerializer(payments, many=True).data
    
    def get_account_activity(self, obj):
        """Get account activity summary"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        
        # Calculate activity metrics
        recent_bookings_count = obj.bookings.filter(booking_date__gte=thirty_days_ago).count()
        recent_login_count = 1 if obj.last_login and obj.last_login >= thirty_days_ago else 0
        
        # Account age
        account_age_days = (now - obj.date_joined).days
        
        # Booking frequency
        if obj.booking_count > 0 and account_age_days > 0:
            avg_bookings_per_month = (obj.booking_count / account_age_days) * 30
        else:
            avg_bookings_per_month = 0
            
        return {
            'account_age_days': account_age_days,
            'recent_activity_30_days': {
                'bookings': recent_bookings_count,
                'logins': recent_login_count
            },
            'lifetime_stats': {
                'avg_bookings_per_month': round(avg_bookings_per_month, 2),
                'customer_since': obj.date_joined.strftime('%B %Y'),
                'last_activity': obj.last_login.isoformat() if obj.last_login else None
            },
            'engagement_level': self._get_engagement_level(obj, recent_bookings_count, obj.booking_count)
        }
    
    def _get_engagement_level(self, obj, recent_bookings, total_bookings):
        """Determine client engagement level"""
        if total_bookings == 0:
            return 'new'
        elif recent_bookings >= 2:
            return 'highly_active'
        elif recent_bookings == 1:
            return 'active'
        elif total_bookings >= 5:
            return 'regular'
        else:
            return 'occasional'
