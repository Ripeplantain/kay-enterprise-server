from django.contrib.auth.models import User
from django.db import models
from django.core.validators import RegexValidator
import uuid

from utils.contants import GENDER_CHOICES

class Client(models.Model):
    """
    Client model for Ghanaian domestic travel app
    """

    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    phone_number = models.CharField(
        max_length=15, 
        unique=True,
        validators=[RegexValidator(
            regex=r'^(\+233|0)(20|23|24|26|27|28|50|53|54|55|56|57|59)\d{7}$',
            message="Enter a valid Ghanaian phone number (e.g., +233201234567 or 0201234567)"
        )]
    )
    email = models.EmailField(unique=True, null=True, blank=True)  # Optional for Ghana
    password_hash = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    other_names = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)

    # Address Information (Ghana-specific)
    area_suburb = models.CharField(max_length=100, blank=True)

    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=200)
    emergency_contact_phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(
            regex=r'^(\+233|0)(20|23|24|26|27|28|50|53|54|55|56|57|59)\d{7}$',
            message="Enter a valid Ghanaian phone number"
        )]
    )
    emergency_contact_relationship = models.CharField(max_length=50)

    # Travel Preferences & Medical
    sms_notifications = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=False)
    whatsapp_notifications = models.BooleanField(default=True)
    
    # App-specific settings
    sms_notifications = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=False)
    whatsapp_notifications = models.BooleanField(default=True)
    
    # Security & Verification
    phone_verified_at = models.DateTimeField(null=True, blank=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clients'
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.phone_number}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.other_names} {self.last_name}".strip()

    def get_masked_phone(self):
        """Return phone number with middle digits masked"""
        if len(self.phone_number) >= 10:
            return f"{self.phone_number[:4]}****{self.phone_number[-3:]}"
        return self.phone_number

    @property
    def is_authenticated(self):
        """Always return True for active clients to work with Django auth"""
        return self.is_active

    @property
    def is_anonymous(self):
        """Always return False for client objects"""
        return False
