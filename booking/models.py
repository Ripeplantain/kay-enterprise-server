from django.db import models
from django.contrib.auth.models import User
from authentication.models import Client
from bus_management.models import Bus, BusTerminal
from datetime import timedelta
import uuid

from utils.contants import BOOKING_STATUS, PAYMENT_STATUS

class Route(models.Model):
    """Bus routes between cities"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)  # e.g., "Accra - Kumasi"
    
    origin_terminal = models.ForeignKey(
        BusTerminal, 
        on_delete=models.CASCADE, 
        related_name='origin_routes'
    )
    destination_terminal = models.ForeignKey(
        BusTerminal, 
        on_delete=models.CASCADE, 
        related_name='destination_routes'
    )
    
    distance_km = models.DecimalField(max_digits=6, decimal_places=2)
    estimated_duration_hours = models.DecimalField(max_digits=4, decimal_places=2)
    
    # Simple pricing - just one fare for your buses
    fare = models.DecimalField(max_digits=8, decimal_places=2)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'routes'
        unique_together = ('origin_terminal', 'destination_terminal')

    def __str__(self):
        return self.name

class Trip(models.Model):
    """Scheduled bus trips"""
    TRIP_STATUS = [
        ('scheduled', 'Scheduled'),
        ('boarding', 'Boarding'),
        ('departed', 'Departed'),
        ('in_transit', 'In Transit'),
        ('arrived', 'Arrived'),
        ('cancelled', 'Cancelled'),
        ('delayed', 'Delayed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip_number = models.CharField(max_length=20, unique=True)
    
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='trips')
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='trips')
    driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='driven_trips')
    conductor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='conducted_trips')
    
    # Schedule
    scheduled_departure = models.DateTimeField()
    scheduled_arrival = models.DateTimeField()
    actual_departure = models.DateTimeField(null=True, blank=True)
    actual_arrival = models.DateTimeField(null=True, blank=True)
    
    total_seats = models.IntegerField()
    available_seats = models.IntegerField()
    fare = models.DecimalField(max_digits=8, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=TRIP_STATUS, default='scheduled')
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'trips'

    def __str__(self):
        return f"{self.trip_number} - {self.route.name}"

class Booking(models.Model):
    """Bus ticket bookings"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking_reference = models.CharField(max_length=20, unique=True)
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='bookings')
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='bookings')
    
    # Passenger details
    passenger_name = models.CharField(max_length=200)
    passenger_phone = models.CharField(max_length=15)
    seat_numbers = models.CharField(max_length=100)
    number_of_seats = models.IntegerField(default=1)
    
    # Pricing
    fare_per_seat = models.DecimalField(max_digits=8, decimal_places=2)
    total_fare = models.DecimalField(max_digits=8, decimal_places=2)
    booking_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=8, decimal_places=2)
    
    booking_status = models.CharField(max_length=20, choices=BOOKING_STATUS, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    booking_date = models.DateTimeField(auto_now_add=True)
    payment_deadline = models.DateTimeField()
    check_in_time = models.DateTimeField(null=True, blank=True)
    
    special_requests = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bookings'

    def __str__(self):
        return f"{self.booking_reference} - {self.passenger_name}"

    def save(self, *args, **kwargs):
        if not self.payment_deadline:
            self.payment_deadline = self.booking_date + timedelta(hours=2)
        super().save(*args, **kwargs)