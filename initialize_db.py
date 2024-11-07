from app import app, db
from models import User, Service, ServiceRequest, Rating
import random

def init_db():
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Create sample users
        providers = [
            {
                'username': 'handyman_joe',
                'phone_number': '+1234567890',
                'email': 'joe@example.com',
                'firebase_uid': 'sample_uid_1',
                'is_provider': True,
                'latitude': 37.7749,
                'longitude': -122.4194
            },
            {
                'username': 'plumber_mike',
                'phone_number': '+1987654321',
                'email': 'mike@example.com',
                'firebase_uid': 'sample_uid_2',
                'is_provider': True,
                'latitude': 37.7833,
                'longitude': -122.4167
            }
        ]
        
        for provider_data in providers:
            provider = User(**provider_data)
            db.session.add(provider)
        
        db.session.commit()
        
        # Create sample services
        services = [
            {
                'title': 'Handyman Services',
                'description': 'General repairs and maintenance for your home.',
                'rate': 50.00,
                'provider_id': 1
            },
            {
                'title': 'Plumbing Services',
                'description': 'Professional plumbing repairs and installations.',
                'rate': 75.00,
                'provider_id': 2
            },
            {
                'title': 'Electrical Work',
                'description': 'Residential electrical repairs and installations.',
                'rate': 65.00,
                'provider_id': 1
            }
        ]
        
        for service_data in services:
            service = Service(**service_data)
            db.session.add(service)
        
        db.session.commit()
        print("Database initialized with sample data!")

if __name__ == '__main__':
    init_db()
