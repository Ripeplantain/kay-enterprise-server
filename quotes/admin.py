from django.contrib import admin
from .models import BusQuote


@admin.register(BusQuote)
class BusQuoteAdmin(admin.ModelAdmin):
    list_display = [
        'reference_number', 'full_name', 'pickup_location', 'destination',
        'travel_date', 'passengers', 'status', 'created_at'
    ]
    list_filter = ['status', 'trip_type', 'preferred_contact_method', 'travel_date', 'created_at']
    search_fields = ['full_name', 'phone_number', 'email', 'reference_number', 'pickup_location', 'destination']
    readonly_fields = ['reference_number', 'created_at', 'updated_at']

    fieldsets = (
        ('Trip Information', {
            'fields': ('pickup_location', 'destination', 'travel_date', 'passengers', 'trip_type')
        }),
        ('Customer Information', {
            'fields': ('full_name', 'phone_number', 'email', 'preferred_contact_method', 'additional_requirements')
        }),
        ('Quote Management', {
            'fields': ('status', 'quote_amount', 'quote_notes')
        }),
        ('System Information', {
            'fields': ('reference_number', 'created_at', 'updated_at')
        }),
    )

    actions = ['mark_as_quoted', 'mark_as_accepted', 'mark_as_completed']

    def mark_as_quoted(self, request, queryset):
        queryset.update(status='quoted')
    mark_as_quoted.short_description = "Mark selected quotes as quoted"

    def mark_as_accepted(self, request, queryset):
        queryset.update(status='accepted')
    mark_as_accepted.short_description = "Mark selected quotes as accepted"

    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
    mark_as_completed.short_description = "Mark selected quotes as completed"
