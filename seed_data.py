from app import app, db
from models import ServiceCategory, ServiceTag

def seed_categories():
    # Main categories
    categories = {
        'Home Services': [
            'Cleaning',
            'Maintenance',
            'Gardening',
            'Interior Design'
        ],
        'Professional Services': [
            'Legal',
            'Financial',
            'Business Consulting',
            'Writing & Translation'
        ],
        'Creative & Digital': [
            'Graphic Design',
            'Web Development',
            'Photography',
            'Video Production'
        ],
        'Personal Services': [
            'Personal Training',
            'Life Coaching',
            'Tutoring',
            'Beauty & Wellness'
        ],
        'Skilled Trade': [
            'Plumbing',
            'Electrical',
            'Carpentry',
            'HVAC'
        ]
    }
    
    # Create main categories and subcategories
    for main_cat, subcats in categories.items():
        main_category = ServiceCategory.query.filter_by(name=main_cat).first()
        if not main_category:
            main_category = ServiceCategory(name=main_cat, description=f"Services related to {main_cat.lower()}")
            db.session.add(main_category)
            db.session.flush()  # Get ID for subcategories
        
        for subcat in subcats:
            if not ServiceCategory.query.filter_by(name=subcat, parent_id=main_category.id).first():
                subcategory = ServiceCategory(
                    name=subcat,
                    description=f"{subcat} services",
                    parent_id=main_category.id
                )
                db.session.add(subcategory)

def seed_tags():
    common_tags = [
        # Skills
        'Certified', 'Licensed', 'Experienced', 'Professional',
        # Service Types
        'Residential', 'Commercial', 'Emergency', 'Remote',
        # Availability
        'Weekends', 'Evenings', '24/7', 'Flexible Hours',
        # Service Features
        'Same Day Service', 'Free Consultation', 'Mobile Service', 'Insurance Coverage',
        # Experience Level
        'Beginner Friendly', 'Advanced', 'Expert', 'Specialist',
        # Additional Qualities
        'Eco-Friendly', 'Pet Friendly', 'Family Owned', 'Multilingual'
    ]
    
    for tag_name in common_tags:
        if not ServiceTag.query.filter_by(name=tag_name).first():
            tag = ServiceTag(name=tag_name)
            db.session.add(tag)

def seed_all():
    print("Starting database seeding...")
    try:
        seed_categories()
        print("Categories seeded successfully")
        seed_tags()
        print("Tags seeded successfully")
        db.session.commit()
        print("All seed data committed successfully")
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding database: {str(e)}")

if __name__ == '__main__':
    with app.app_context():
        seed_all()
