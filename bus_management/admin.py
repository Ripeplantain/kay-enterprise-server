from django.contrib import admin

from .models import BusTerminal, Bus

@admin.register(BusTerminal)
class BusTerminalAdmin(admin.ModelAdmin):
    list_display = ('name', 'terminal_type', 'region', 'city_town', 'area_suburb', 'phone_number', 'is_active')
    search_fields = ('name', 'city_town', 'area_suburb')
    list_filter = ('terminal_type', 'region', 'is_active')
    
@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ('name', 'registration_number', 'bus_number', 'bus_type', 'make_model', 'total_seats', 'available_seats', 'status')
    search_fields = ('name', 'registration_number', 'bus_number', 'make_model')
    list_filter = ('bus_type', 'status')
    readonly_fields = ('registration_number',)

