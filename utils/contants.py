GHANA_REGIONS = [
    ('greater_accra', 'Greater Accra'),
    ('ashanti', 'Ashanti'),
    ('western', 'Western'),
    ('central', 'Central'),
    ('volta', 'Volta'),
    ('eastern', 'Eastern'),
    ('northern', 'Northern'),
    ('upper_east', 'Upper East'),
    ('upper_west', 'Upper West'),
    ('brong_ahafo', 'Brong Ahafo'),
    ('western_north', 'Western North'),
    ('ahafo', 'Ahafo'),
    ('bono_east', 'Bono East'),
    ('oti', 'Oti'),
    ('north_east', 'North East'),
    ('savannah', 'Savannah'),
]

GENDER_CHOICES = [
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
]

BUS_TYPES = [
    ('standard', 'Standard Bus'),
    ('luxury', 'Luxury Bus'),
    ('vip', 'VIP Bus'),
    ('executive', 'Executive Bus'),
    ('sleeper', 'Sleeper Bus'),
]

BUS_STATUS = [
    ('active', 'Active'),
    ('maintenance', 'Under Maintenance'),
    ('out_of_service', 'Out of Service'),
    ('retired', 'Retired'),
]

TERMINAL_TYPES = [
    ('main_station', 'Main Station'),
    ('sub_station', 'Sub Station'),
    ('pickup_point', 'Pickup Point'),
    ('drop_off', 'Drop-off Point'),
]

BOOKING_STATUS = [
    ('pending', 'Pending Payment'),
    ('confirmed', 'Confirmed'),
    ('cancelled', 'Cancelled'),
    ('refunded', 'Refunded'),
    ('completed', 'Completed'),
    ('no_show', 'No Show'),
]

PAYMENT_STATUS = [
    ('pending', 'Pending'),
    ('paid', 'Paid'),
    ('failed', 'Failed'),
    ('refunded', 'Refunded'),
    ('partial', 'Partial Payment'),
]

LUGGAGE_STATUS = [
    ('registered', 'Registered'),
    ('loaded', 'Loaded onto Bus'),
    ('in_transit', 'In Transit'),
    ('arrived', 'Arrived at Destination'),
    ('collected', 'Collected by Owner'),
    ('unclaimed', 'Unclaimed'),
    ('lost', 'Lost'),
    ('damaged', 'Damaged'),
]

FRAGILE_LEVELS = [
    ('none', 'Not Fragile'),
    ('low', 'Low Fragility'),
    ('medium', 'Medium Fragility'),
    ('high', 'High Fragility'),
    ('very_high', 'Very High Fragility'),
]

PAYMENT_METHODS = [
    ('mobile_money', 'Mobile Money'),
    ('card', 'Credit/Debit Card'),
    ('bank_transfer', 'Bank Transfer'),
    ('cash', 'Cash'),
    ('wallet', 'Digital Wallet'),
]

MOBILE_MONEY_PROVIDERS = [
    ('mtn_momo', 'MTN Mobile Money'),
    ('vodafone_cash', 'Vodafone Cash'),
    ('airteltigo_money', 'AirtelTigo Money'),
]
