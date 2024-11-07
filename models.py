from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    firebase_uid = db.Column(db.String(128), unique=True, nullable=False)
    verification_code = db.Column(db.String(6))  # Store temporary verification code
    verification_code_timestamp = db.Column(db.DateTime)  # For code expiration
    is_provider = db.Column(db.Boolean, default=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    services = db.relationship('Service', backref='provider', lazy=True)
    
    def set_verification_code(self, code):
        self.verification_code = code
        self.verification_code_timestamp = datetime.utcnow()
        
    def check_verification_code(self, code):
        if not self.verification_code or not self.verification_code_timestamp:
            return False
        time_diff = (datetime.utcnow() - self.verification_code_timestamp).total_seconds()
        return self.verification_code == code and time_diff <= 300  # 5 minutes expiration

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    rate = db.Column(db.Float, nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    requests = db.relationship('ServiceRequest', backref='service', lazy=True)

class ServiceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, declined, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)