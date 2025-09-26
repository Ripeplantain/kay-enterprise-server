from django.db import models
from authentication.models import Client


class Route(models.Model):
    name = models.CharField(max_length=200)
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    distance_km = models.DecimalField(max_digits=8, decimal_places=2)
    estimated_duration_hours = models.DecimalField(max_digits=4, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.origin} - {self.destination}"


class Bus(models.Model):
    BUS_TYPE_CHOICES = [
        ('express', 'Express'),
        ('vip', 'VIP'),
    ]

    plate_number = models.CharField(max_length=20, unique=True)
    bus_type = models.CharField(max_length=20, choices=BUS_TYPE_CHOICES, default='express')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.plate_number} ({self.bus_type})"

    @property
    def total_seats(self):
        """Get total seats based on bus type"""
        return 30 if self.bus_type == 'express' else 45

    def create_seats(self):
        """Create seats for this bus based on bus type"""
        # Clear existing seats
        self.seats.all().delete()

        if self.bus_type == 'express':
            # Express: 30 seats numbered 1-30
            for seat_num in range(1, 31):
                # Alternate between window and aisle seats
                seat_type = 'window' if seat_num % 2 == 1 else 'aisle'
                Seat.objects.create(
                    bus=self,
                    seat_number=str(seat_num),
                    seat_type=seat_type
                )
        else:  # VIP
            # VIP: 45 seats numbered 1-45
            for seat_num in range(1, 46):
                # Alternate between window and aisle seats
                seat_type = 'window' if seat_num % 2 == 1 else 'aisle'
                Seat.objects.create(
                    bus=self,
                    seat_number=str(seat_num),
                    seat_type=seat_type
                )

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Create seats if this is a new bus or if seats don't exist
        if is_new or not self.seats.exists():
            self.create_seats()


class Seat(models.Model):
    SEAT_TYPE_CHOICES = [
        ('window', 'Window'),
        ('aisle', 'Aisle'),
        ('middle', 'Middle'),
    ]
    
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='seats')
    seat_number = models.CharField(max_length=5)
    seat_type = models.CharField(max_length=10, choices=SEAT_TYPE_CHOICES, default='aisle')
    is_available = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('bus', 'seat_number')

    def __str__(self):
        return f"{self.bus.plate_number} - Seat {self.seat_number}"


class Trip(models.Model):
    TRIP_STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('boarding', 'Boarding'),
        ('in_transit', 'In Transit'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    departure_datetime = models.DateTimeField()
    arrival_datetime = models.DateTimeField()
    price_per_seat = models.DecimalField(max_digits=10, decimal_places=2)
    available_seats = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=TRIP_STATUS_CHOICES, default='scheduled')
    pickup_points = models.JSONField(default=list)  # [{"name": "Terminal A", "time": "10:00"}, ...]
    drop_points = models.JSONField(default=list)    # [{"name": "Terminal B", "time": "14:00"}, ...]
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.route} - {self.departure_datetime.strftime('%Y-%m-%d %H:%M')}"


class LuggageType(models.Model):
    name = models.CharField(max_length=100)
    max_weight_kg = models.DecimalField(max_digits=5, decimal_places=2)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} (Max {self.max_weight_kg}kg)"


class Booking(models.Model):
    BOOKING_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    booking_reference = models.CharField(max_length=20, unique=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    pickup_point_id = models.CharField(max_length=10, null=True, blank=True)
    drop_point_id = models.CharField(max_length=10, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=BOOKING_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.booking_reference} - {self.client}"


class BookingLuggage(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='luggage_items')
    has_luggage = models.BooleanField(default=False)
    luggage_count = models.IntegerField(default=0)
    special_items = models.JSONField(default=list)  # e.g., ["sound_system", "electronics"]
    luggage_handling_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    cargo_van_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    special_items_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_luggage_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    luggage_notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.booking.booking_reference} - Luggage ({self.luggage_count} items)"
