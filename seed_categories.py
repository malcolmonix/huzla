from app import app, db
from models import ServiceCategory

def seed_categories():
    # Create main categories
    categories = {
        'Home Services': {
            'description': 'Services related to home maintenance and improvement',
            'subcategories': [
                ('Plumbing', 'Water system installation, repair and maintenance'),
                ('Electrical', 'Electrical installation and repair services'),
                ('Cleaning', 'Home cleaning and maintenance services'),
                ('Landscaping', 'Garden and outdoor maintenance services'),
                ('HVAC', 'Heating, ventilation, and air conditioning services')
            ]
        },
        'Professional Services': {
            'description': 'Business and professional services',
            'subcategories': [
                ('Legal', 'Legal consultation and services'),
                ('Financial', 'Financial advisory and accounting services'),
                ('Consulting', 'Business consulting services'),
                ('Marketing', 'Marketing and advertising services'),
                ('IT Services', 'Information technology services')
            ]
        },
        'Personal Services': {
            'description': 'Personal care and wellness services',
            'subcategories': [
                ('Beauty', 'Beauty and cosmetic services'),
                ('Fitness', 'Personal training and fitness services'),
                ('Healthcare', 'Healthcare and medical services'),
                ('Education', 'Tutoring and educational services'),
                ('Pet Care', 'Pet grooming and care services')
            ]
        },
        'Creative Services': {
            'description': 'Creative and artistic services',
            'subcategories': [
                ('Photography', 'Photography and videography services'),
                ('Design', 'Graphic and web design services'),
                ('Music', 'Music lessons and performance services'),
                ('Writing', 'Content writing and editing services'),
                ('Art', 'Fine arts and crafts services')
            ]
        }
    }

    with app.app_context():
        # Clear existing categories
        ServiceCategory.query.delete()
        db.session.commit()

        # Add main categories and their subcategories
        for main_cat, details in categories.items():
            main_category = ServiceCategory(
                name=main_cat,
                description=details['description']
            )
            db.session.add(main_category)
            db.session.flush()  # Get ID for main category

            # Add subcategories
            for sub_name, sub_desc in details['subcategories']:
                subcategory = ServiceCategory(
                    name=sub_name,
                    description=sub_desc,
                    parent_id=main_category.id
                )
                db.session.add(subcategory)

        db.session.commit()
        print("Service categories seeded successfully!")

if __name__ == "__main__":
    seed_categories()
