from django.contrib import admin
from .models import Route, Bus, Seat, Trip, LuggageType, Booking, BookingLuggage


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['name', 'origin', 'destination', 'distance_km', 'is_active']
    list_filter = ['is_active', 'origin', 'destination']
    search_fields = ['name', 'origin', 'destination']


@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ['plate_number', 'bus_type', 'total_seats', 'is_active']
    list_filter = ['bus_type', 'is_active']
    search_fields = ['plate_number']


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ['bus', 'seat_number', 'seat_type', 'is_available']
    list_filter = ['seat_type', 'is_available', 'bus__bus_type']
    search_fields = ['bus__plate_number', 'seat_number']


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ['route', 'bus', 'departure_datetime', 'price_per_seat', 'available_seats', 'status']
    list_filter = ['status', 'bus__bus_type', 'route']
    search_fields = ['route__name', 'bus__plate_number']
    date_hierarchy = 'departure_datetime'


@admin.register(LuggageType)
class LuggageTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'max_weight_kg', 'price', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']


class BookingLuggageInline(admin.TabularInline):
    model = BookingLuggage
    extra = 0


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['booking_reference', 'client', 'trip', 'seat', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'trip__route']
    search_fields = ['booking_reference', 'client__user__email', 'trip__route__name']
    readonly_fields = ['booking_reference', 'created_at', 'updated_at']
    inlines = [BookingLuggageInline]
