from django.db import models
from django.core.validators import MinLengthValidator, EmailValidator


class Agent(models.Model):
    ID_TYPE_CHOICES = [
        ('Ghana Card', 'Ghana Card'),
        ('Voter ID', 'Voter ID'),
        ('Passport', 'Passport'),
        ("Driver's License", "Driver's License"),
    ]
    
    MOBILE_MONEY_PROVIDERS = [
        ('MTN Mobile Money', 'MTN Mobile Money'),
        ('Vodafone Cash', 'Vodafone Cash'),
        ('AirtelTigo Money', 'AirtelTigo Money'),
    ]
    
    AVAILABILITY_CHOICES = [
        ('Full-time (8+ hours/day)', 'Full-time (8+ hours/day)'),
        ('Part-time (4-7 hours/day)', 'Part-time (4-7 hours/day)'),
        ('Weekends only', 'Weekends only'),
        ('Flexible hours', 'Flexible hours'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    full_name = models.CharField(max_length=255, validators=[MinLengthValidator(2)])
    phone_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    id_type = models.CharField(max_length=20, choices=ID_TYPE_CHOICES)
    id_number = models.CharField(max_length=50)
    region = models.CharField(max_length=100)
    city_town = models.CharField(max_length=100, validators=[MinLengthValidator(2)])
    area_suburb = models.CharField(max_length=100, blank=True, null=True)
    mobile_money_provider = models.CharField(max_length=20, choices=MOBILE_MONEY_PROVIDERS)
    mobile_money_number = models.CharField(max_length=20)
    availability = models.CharField(max_length=30, choices=AVAILABILITY_CHOICES)
    referral_code = models.CharField(max_length=20, blank=True, null=True)
    why_join = models.TextField(validators=[MinLengthValidator(10)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference_number = models.CharField(max_length=20, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'agents'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.full_name} - {self.reference_number}"
    
    def save(self, *args, **kwargs):
        if not self.reference_number:
            self.reference_number = self.generate_reference_number()
        super().save(*args, **kwargs)
    
    def generate_reference_number(self):
        from datetime import datetime
        year = datetime.now().year
        month = datetime.now().month
        
        last_agent = Agent.objects.filter(
            reference_number__startswith=f'AG{year}{month:02d}'
        ).order_by('-reference_number').first()
        
        if last_agent:
            last_number = int(last_agent.reference_number[-3:])
            new_number = last_number + 1
        else:
            new_number = 1
            
        return f'AG{year}{month:02d}{new_number:03d}'
