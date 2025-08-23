from django.db import models
from django.contrib.auth.models import User
from booking.models import Booking
import uuid

from utils.contants import FRAGILE_LEVELS, LUGGAGE_STATUS

class LuggageType(models.Model):
    """Types of luggage that can be transported"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    # Size and weight limits
    max_weight_kg = models.DecimalField(max_digits=6, decimal_places=2)
    max_length_cm = models.DecimalField(max_digits=6, decimal_places=2)
    max_width_cm = models.DecimalField(max_digits=6, decimal_places=2)
    max_height_cm = models.DecimalField(max_digits=6, decimal_places=2)
    
    # Pricing
    base_price = models.DecimalField(max_digits=6, decimal_places=2)
    price_per_kg = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'luggage_types'

    def __str__(self):
        return self.name

class Luggage(models.Model):
    """Individual luggage items"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    luggage_tag = models.CharField(max_length=20, unique=True)
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='luggage_items')
    luggage_type = models.ForeignKey(LuggageType, on_delete=models.CASCADE)
    
    # Physical properties
    description = models.TextField()
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2)
    length_cm = models.DecimalField(max_digits=6, decimal_places=2)
    width_cm = models.DecimalField(max_digits=6, decimal_places=2)
    height_cm = models.DecimalField(max_digits=6, decimal_places=2)
    
    # Special handling
    is_fragile = models.BooleanField(default=False)
    fragile_level = models.CharField(max_length=20, choices=FRAGILE_LEVELS, default='none')
    is_valuable = models.BooleanField(default=False)
    declared_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    special_instructions = models.TextField(blank=True)
    requires_upright = models.BooleanField(default=False)
    temperature_sensitive = models.BooleanField(default=False)
    
    status = models.CharField(max_length=20, choices=LUGGAGE_STATUS, default='registered')
    current_location = models.CharField(max_length=200, blank=True)
    
    # Pricing
    luggage_fee = models.DecimalField(max_digits=8, decimal_places=2)
    insurance_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    
    # Timestamps
    registered_at = models.DateTimeField(auto_now_add=True)
    loaded_at = models.DateTimeField(null=True, blank=True)
    arrived_at = models.DateTimeField(null=True, blank=True)
    collected_at = models.DateTimeField(null=True, blank=True)
    collected_by = models.CharField(max_length=200, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'luggage'

    def __str__(self):
        return f"{self.luggage_tag} - {self.description[:30]}"

class LuggageTracking(models.Model):
    """Tracking history for luggage items"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    luggage = models.ForeignKey(Luggage, on_delete=models.CASCADE, related_name='tracking_history')
    
    location = models.CharField(max_length=200)
    status = models.CharField(max_length=50)
    notes = models.TextField(blank=True)
    
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'luggage_tracking'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.luggage.luggage_tag} - {self.status}"
