from app.models import Region, State

NIGERIA_REGIONS = {
    'North Central': ['Benue', 'FCT', 'Kogi', 'Kwara', 'Nasarawa', 'Niger', 'Plateau'],
    'North East': ['Adamawa', 'Bauchi', 'Borno', 'Gombe', 'Taraba', 'Yobe'],
    'North West': ['Kaduna', 'Katsina', 'Kano', 'Kebbi', 'Sokoto', 'Jigawa', 'Zamfara'],
    'South East': ['Abia', 'Anambra', 'Ebonyi', 'Enugu', 'Imo'],
    'South South': ['Akwa Ibom', 'Bayelsa', 'Cross River', 'Delta', 'Edo', 'Rivers'],
    'South West': ['Ekiti', 'Lagos', 'Ogun', 'Ondo', 'Osun', 'Oyo']
}

def init_locations():
    for region_name, states in NIGERIA_REGIONS.items():
        region = Region(name=region_name)
        db.session.add(region)
        db.session.flush()
        
        for state_name in states:
            state = State(name=state_name, region_id=region.id)
            db.session.add(state)
    
    db.session.commit() 