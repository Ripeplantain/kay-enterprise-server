from django.db import models
from django.core.validators import RegexValidator
import uuid

from utils.contants import BUS_STATUS, BUS_TYPES, GHANA_REGIONS, TERMINAL_TYPES

class BusTerminal(models.Model):
    """Bus terminals and stations across Ghana"""

    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    terminal_type = models.CharField(max_length=20, choices=TERMINAL_TYPES)
    region = models.CharField(max_length=20, choices=GHANA_REGIONS)
    city_town = models.CharField(max_length=100)
    area_suburb = models.CharField(max_length=100)
    address = models.TextField()
    gps_coordinates = models.CharField(max_length=50, blank=True)
    
    # Facilities
    has_waiting_area = models.BooleanField(default=True)
    has_restroom = models.BooleanField(default=True)
    has_food_court = models.BooleanField(default=False)
    has_parking = models.BooleanField(default=True)
    has_luggage_storage = models.BooleanField(default=True)
    
    phone_number = models.CharField(max_length=15, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bus_terminals'

    def __str__(self):
        return f"{self.name} - {self.city_town}"

class Bus(models.Model):
    """Your company's buses"""


    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Bus details
    name = models.CharField(max_length=100)  # e.g., "Kay Enterprise Bus 1"
    registration_number = models.CharField(max_length=20, unique=True)  # Ghana plate number
    bus_number = models.CharField(max_length=20)  # Your internal number like "KE001"
    bus_type = models.CharField(max_length=20, choices=BUS_TYPES)
    make_model = models.CharField(max_length=100)  # e.g., "Mercedes Benz OH1518"
    year_manufactured = models.IntegerField()
    
    # Capacity
    total_seats = models.IntegerField()
    available_seats = models.IntegerField()
    
    # Features
    has_ac = models.BooleanField(default=True)
    has_wifi = models.BooleanField(default=False)
    has_entertainment = models.BooleanField(default=False)
    has_charging_ports = models.BooleanField(default=False)
    has_restroom = models.BooleanField(default=False)
    
    # Luggage capacity
    luggage_compartment_capacity = models.DecimalField(
        max_digits=6, decimal_places=2,
        help_text="Capacity in cubic meters"
    )
    max_luggage_weight = models.DecimalField(
        max_digits=6, decimal_places=2,
        help_text="Maximum luggage weight in kg"
    )
    
    status = models.CharField(max_length=20, choices=BUS_STATUS, default='active')
    last_maintenance_date = models.DateField(null=True, blank=True)
    next_maintenance_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'buses'

    def __str__(self):
        return f"{self.name} ({self.registration_number})"