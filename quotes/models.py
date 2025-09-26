from django.db import models
from django.core.validators import MinLengthValidator, MinValueValidator, MaxValueValidator


class BusQuote(models.Model):
    TRIP_TYPE_CHOICES = [
        ('One-way', 'One-way'),
        ('Round-trip', 'Round-trip'),
        ('Multi-day charter', 'Multi-day charter'),
    ]

    CONTACT_METHOD_CHOICES = [
        ('Phone', 'Phone'),
        ('Email', 'Email'),
        ('WhatsApp', 'WhatsApp'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('quoted', 'Quoted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]

    pickup_location = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    travel_date = models.DateField()
    passengers = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    trip_type = models.CharField(max_length=20, choices=TRIP_TYPE_CHOICES)

    full_name = models.CharField(max_length=255, validators=[MinLengthValidator(2)])
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    preferred_contact_method = models.CharField(max_length=10, choices=CONTACT_METHOD_CHOICES)
    additional_requirements = models.TextField(blank=True)

    reference_number = models.CharField(max_length=20, unique=True, editable=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    quote_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quote_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bus_quotes'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.reference_number:
            from django.utils import timezone
            now = timezone.now()
            prefix = f"BQ{now.year}{now.month:02d}"
            last_quote = BusQuote.objects.filter(
                reference_number__startswith=prefix
            ).order_by('-reference_number').first()

            if last_quote:
                last_number = int(last_quote.reference_number[-3:])
                new_number = last_number + 1
            else:
                new_number = 1

            self.reference_number = f"{prefix}{new_number:03d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.pickup_location} to {self.destination} ({self.reference_number})"
