from django.db import models
from booking.models import Booking
import uuid

from utils.contants import MOBILE_MONEY_PROVIDERS, PAYMENT_METHODS

class Payment(models.Model):
    """Payment records for bookings"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_reference = models.CharField(max_length=50, unique=True)
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='GHS')
    
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    mobile_money_provider = models.CharField(max_length=20, choices=MOBILE_MONEY_PROVIDERS, blank=True)
    mobile_money_number = models.CharField(max_length=15, blank=True)
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('successful', 'Successful'),
            ('failed', 'Failed'),
            ('cancelled', 'Cancelled'),
            ('refunded', 'Refunded'),
        ],
        default='pending'
    )
    
    gateway_response = models.JSONField(null=True, blank=True)
    gateway_reference = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'payments'

    def __str__(self):
        return f"{self.payment_reference} - GHS {self.amount}"