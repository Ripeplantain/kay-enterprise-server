from django.contrib import admin

from .models import Route, Trip, Booking

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('name', 'origin_terminal', 'destination_terminal', 'distance_km', 'estimated_duration_hours', 'fare')
    search_fields = ('name', 'origin_terminal__name', 'destination_terminal__name')
    list_filter = ('origin_terminal', 'destination_terminal')
    
@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('trip_number', 'bus', 'route', 'scheduled_departure', 'scheduled_arrival', 'status')
    search_fields = ('trip_number', 'bus__name', 'route__name')
    list_filter = ('bus', 'route', 'status')
    
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_reference', 'client', 'trip', 'passenger_name', 'passenger_phone', 'booking_status', 'payment_status')
    search_fields = ('booking_reference', 'client__username', 'trip__trip_number')
    list_filter = ('client', 'trip', 'booking_status', 'payment_status')
    readonly_fields = ('booking_reference',)
