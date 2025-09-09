#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime, date
import hashlib

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from authentication.models import Client
from django.contrib.auth.models import User

def create_test_clients():
    print("Creating test clients...")
    
    # Create sample client data
    clients_data = [
        {
            "phone_number": "+233201234567",
            "email": "kwame.asante@email.com",
            "first_name": "Kwame",
            "last_name": "Asante",
            "other_names": "Kofi",
            "date_of_birth": date(1990, 5, 15),
            "gender": "M",
            "region": "greater_accra",
            "city_town": "Accra",
            "area_suburb": "East Legon",
            "emergency_contact_name": "Ama Asante",
            "emergency_contact_phone": "+233241234567",
            "emergency_contact_relationship": "Sister",
            "password": "password123"
        },
        {
            "phone_number": "+233241234568",
            "email": "akosua.mensah@email.com",
            "first_name": "Akosua",
            "last_name": "Mensah",
            "other_names": "",
            "date_of_birth": date(1985, 8, 22),
            "gender": "F",
            "region": "ashanti",
            "city_town": "Kumasi",
            "area_suburb": "Bantama",
            "emergency_contact_name": "Yaw Mensah",
            "emergency_contact_phone": "+233201234568",
            "emergency_contact_relationship": "Brother",
            "password": "password123"
        },
        {
            "phone_number": "+233501234567",
            "email": "kofi.boateng@email.com",
            "first_name": "Kofi",
            "last_name": "Boateng",
            "other_names": "Kwaku",
            "date_of_birth": date(1988, 12, 10),
            "gender": "M",
            "region": "central",
            "city_town": "Cape Coast",
            "area_suburb": "University Area",
            "emergency_contact_name": "Efua Boateng",
            "emergency_contact_phone": "+233271234567",
            "emergency_contact_relationship": "Mother",
            "password": "password123"
        }
    ]
    
    created_clients = []
    for client_data in clients_data:
        password = client_data.pop('password')
        
        # Check if client already exists
        if Client.objects.filter(phone_number=client_data['phone_number']).exists():
            print(f"Client with phone {client_data['phone_number']} already exists")
            continue
        
        # Create Django User first
        user = User.objects.create_user(
            username=client_data['phone_number'],
            email=client_data['email'],
            first_name=client_data['first_name'],
            last_name=client_data['last_name'],
            password=password
        )
        
        # Hash password for client model
        client_data['password_hash'] = hashlib.sha256(password.encode()).hexdigest()
        client_data['user'] = user
        client_data['is_verified'] = True  # Auto-verify test clients
        
        client = Client.objects.create(**client_data)
        created_clients.append(client)
        print(f"Created client: {client.full_name} - {client.phone_number}")
    
    print(f"\nTest clients creation completed!")
    print(f"Created {len(created_clients)} test clients")
    
    print("\nTest login credentials:")
    for client in created_clients:
        print(f"Phone: {client.phone_number} | Password: password123")
    
    return created_clients

if __name__ == "__main__":
    create_test_clients()