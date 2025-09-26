#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from booking.models import Route, Bus, Seat, Trip, LuggageType, Booking, BookingLuggage
from authentication.models import Client, User

def create_dummy_data():
    print("Creating dummy data...")
    
    # Create Routes
    routes_data = [
        {"name": "Accra - Kumasi Express", "origin": "Accra", "destination": "Kumasi", "distance_km": 250, "estimated_duration_hours": 4},
        {"name": "Accra - Cape Coast Highway", "origin": "Accra", "destination": "Cape Coast", "distance_km": 165, "estimated_duration_hours": 2.5},
        {"name": "Kumasi - Tamale Route", "origin": "Kumasi", "destination": "Tamale", "distance_km": 380, "estimated_duration_hours": 6},
        {"name": "Takoradi - Accra", "origin": "Takoradi", "destination": "Accra", "distance_km": 232, "estimated_duration_hours": 3.5},
        {"name": "Ho - Accra", "origin": "Ho", "destination": "Accra", "distance_km": 165, "estimated_duration_hours": 2.5},
    ]
    
    routes = []
    for route_data in routes_data:
        route, created = Route.objects.get_or_create(
            name=route_data["name"],
            defaults=route_data
        )
        routes.append(route)
        if created:
            print(f"Created route: {route.name}")
    
    # Create Buses
    buses_data = [
        {"plate_number": "GH-101-24", "bus_type": "express"},
        {"plate_number": "GH-202-24", "bus_type": "vip"},
        {"plate_number": "GH-303-24", "bus_type": "express"},
        {"plate_number": "GH-404-24", "bus_type": "vip"},
        {"plate_number": "GH-505-24", "bus_type": "express"},
        {"plate_number": "GH-606-24", "bus_type": "vip"},
    ]

    buses = []
    for bus_data in buses_data:
        bus, created = Bus.objects.get_or_create(
            plate_number=bus_data["plate_number"],
            defaults=bus_data
        )
        buses.append(bus)
        if created:
            print(f"Created bus: {bus.plate_number} ({bus.bus_type}) with {bus.total_seats} seats")
        else:
            print(f"Bus already exists: {bus.plate_number} ({bus.bus_type}) with {bus.total_seats} seats")
    
    # Create Luggage Types
    luggage_types_data = [
        {"name": "Small Bag", "max_weight_kg": 10, "price": 15},  # GH₵15
        {"name": "Medium Bag", "max_weight_kg": 20, "price": 25},  # GH₵25
        {"name": "Large Bag", "max_weight_kg": 30, "price": 35},   # GH₵35
        {"name": "Extra Large", "max_weight_kg": 50, "price": 60}, # GH₵60
        {"name": "Fragile Item", "max_weight_kg": 15, "price": 40}, # GH₵40
    ]
    
    luggage_types = []
    for luggage_data in luggage_types_data:
        luggage_type, created = LuggageType.objects.get_or_create(
            name=luggage_data["name"],
            defaults=luggage_data
        )
        luggage_types.append(luggage_type)
        if created:
            print(f"Created luggage type: {luggage_type.name}")
    
    # Create Trips
    base_date = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
    
    trips_data = [
        {
            "route": routes[0],  # Accra - Kumasi
            "bus": buses[0],
            "departure_datetime": base_date + timedelta(days=1),
            "arrival_datetime": base_date + timedelta(days=1, hours=4),
            "price_per_seat": 85,  # GH₵85
            "pickup_points": [
                {"name": "Accra Central Station", "time": "06:00"},
                {"name": "Circle VIP Station", "time": "06:30"},
                {"name": "Tema Station", "time": "07:00"}
            ],
            "drop_points": [
                {"name": "Kumasi Central Terminal", "time": "10:00"},
                {"name": "Kejetia Market", "time": "10:30"},
                {"name": "KNUST Junction", "time": "11:00"}
            ]
        },
        {
            "route": routes[0],  # Accra - Kumasi (Evening)
            "bus": buses[3],
            "departure_datetime": base_date + timedelta(days=1, hours=16),
            "arrival_datetime": base_date + timedelta(days=1, hours=20),
            "price_per_seat": 95,  # GH₵95
            "pickup_points": [
                {"name": "Accra Central Station", "time": "16:00"},
                {"name": "Circle VIP Station", "time": "16:30"}
            ],
            "drop_points": [
                {"name": "Kumasi Central Terminal", "time": "20:00"},
                {"name": "Kejetia Market", "time": "20:30"}
            ]
        },
        {
            "route": routes[1],  # Accra - Cape Coast
            "bus": buses[1],
            "departure_datetime": base_date + timedelta(days=1, hours=8),
            "arrival_datetime": base_date + timedelta(days=1, hours=10, minutes=30),
            "price_per_seat": 45,  # GH₵45
            "pickup_points": [
                {"name": "Kaneshie Station", "time": "08:00"},
                {"name": "Mallam Junction", "time": "08:15"}
            ],
            "drop_points": [
                {"name": "Cape Coast Central", "time": "10:30"},
                {"name": "University of Cape Coast", "time": "10:45"}
            ]
        },
        {
            "route": routes[2],  # Kumasi - Tamale
            "bus": buses[2],
            "departure_datetime": base_date + timedelta(days=2, hours=7),
            "arrival_datetime": base_date + timedelta(days=2, hours=13),
            "price_per_seat": 120,  # GH₵120
            "pickup_points": [
                {"name": "Kumasi Central Terminal", "time": "07:00"},
                {"name": "Tech Junction", "time": "07:30"}
            ],
            "drop_points": [
                {"name": "Tamale Central Station", "time": "13:00"},
                {"name": "University for Development Studies", "time": "13:30"}
            ]
        },
        {
            "route": routes[3],  # Takoradi - Accra
            "bus": buses[4],
            "departure_datetime": base_date + timedelta(days=1, hours=10),
            "arrival_datetime": base_date + timedelta(days=1, hours=13, minutes=30),
            "price_per_seat": 60,  # GH₵60
            "pickup_points": [
                {"name": "Takoradi Market Circle", "time": "10:00"},
                {"name": "European Hospital", "time": "10:20"}
            ],
            "drop_points": [
                {"name": "Accra Central Station", "time": "13:30"},
                {"name": "37 Station", "time": "14:00"}
            ]
        }
    ]
    
    trips = []
    for trip_data in trips_data:
        # Set available seats to total bus seats
        trip_data["available_seats"] = trip_data["bus"].total_seats
        
        trip, created = Trip.objects.get_or_create(
            route=trip_data["route"],
            bus=trip_data["bus"],
            departure_datetime=trip_data["departure_datetime"],
            defaults=trip_data
        )
        trips.append(trip)
        if created:
            print(f"Created trip: {trip.route.name} on {trip.departure_datetime}")
    
    print(f"\nDummy data creation completed!")
    print(f"Created {len(routes)} routes")
    print(f"Created {len(buses)} buses with seats")
    print(f"Created {len(luggage_types)} luggage types")
    print(f"Created {len(trips)} trips")
    print("\nYou can now:")
    print("1. Search for trips: GET /api/booking/search/?origin=Accra&destination=Kumasi&departure_date=2025-09-08")
    print("2. View trip details: GET /api/booking/trips/{id}/")
    print("3. Check seat availability: GET /api/booking/trips/{id}/seats/")
    print("4. Access admin panel: http://localhost:8000/admin/")

if __name__ == "__main__":
    create_dummy_data()