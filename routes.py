from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Service, ServiceRequest, Rating
from urllib.parse import urlparse
import requests
import re

def validate_password(password):
    """Check if password meets requirements."""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    return True

def verify_firebase_token(id_token):
    """Verify Firebase ID token."""
    try:
        response = requests.get(
            f'https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={app.config["FIREBASE_API_KEY"]}',
            params={'idToken': id_token}
        )
        if response.status_code == 200:
            user_data = response.json()['users'][0]
            return user_data
        return None
    except Exception:
        return None

@app.route('/')
def index():
    return redirect(url_for('service_list'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        id_token = request.form.get('id_token')
        if not id_token:
            flash('No ID token provided', 'danger')
            return redirect(url_for('login'))

        firebase_user = verify_firebase_token(id_token)
        if not firebase_user:
            flash('Invalid token', 'danger')
            return redirect(url_for('login'))

        user = User.query.filter_by(firebase_uid=firebase_user['localId']).first()
        if not user:
            flash('User not registered', 'danger')
            return redirect(url_for('login'))

        login_user(user)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('index')

        flash('Logged in successfully!', 'success')
        return redirect(next_page)
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        id_token = request.form.get('id_token')
        username = request.form.get('username')
        phone_number = request.form.get('phone_number')
        email = request.form.get('email')
        is_provider = request.form.get('is_provider') == 'on'
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        
        if not all([id_token, username, phone_number, email, latitude, longitude]):
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('register'))

        firebase_user = verify_firebase_token(id_token)
        if not firebase_user:
            flash('Invalid token', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(phone_number=phone_number).first():
            flash('Phone number already registered', 'danger')
            return redirect(url_for('register'))

        # Validate password
        password = request.form.get('password')
        if not validate_password(password):
            flash('Password must be at least 8 characters long and include uppercase, lowercase, and numbers', 'danger')
            return redirect(url_for('register'))

        try:
            user = User(
                username=username,
                phone_number=phone_number,
                email=email,
                firebase_uid=firebase_user['localId'],
                is_provider=is_provider,
                latitude=float(latitude),
                longitude=float(longitude)
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('index'))

        except Exception:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
    flash('Logged out successfully', 'info')
    return redirect(url_for('index'))

@app.route('/services')
def service_list():
    services = Service.query.all()
    return render_template('service_list.html', services=services)

@app.route('/service/<int:id>')
def service_detail(id):
    service = Service.query.get_or_404(id)
    return render_template('service_detail.html', service=service)

@app.route('/api/services')
def api_services():
    services = Service.query.all()
    return jsonify([{
        'id': s.id,
        'title': s.title,
        'provider': s.provider.username,
        'rate': s.rate,
        'lat': s.provider.latitude,
        'lng': s.provider.longitude
    } for s in services])

@app.route('/service/request/<int:service_id>', methods=['POST'])
@login_required
def request_service(service_id):
    service = Service.query.get_or_404(service_id)
    if service.provider_id == current_user.id:
        flash('You cannot request your own service')
        return redirect(url_for('service_detail', id=service_id))
    
    request = ServiceRequest(service_id=service_id, client_id=current_user.id)
    db.session.add(request)
    db.session.commit()
    flash('Service requested successfully')
    return redirect(url_for('service_detail', id=service_id))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_provider:
        services = Service.query.filter_by(provider_id=current_user.id).all()
        requests = ServiceRequest.query.filter(
            ServiceRequest.service_id.in_([s.id for s in services])
        ).all()
    else:
        requests = ServiceRequest.query.filter_by(client_id=current_user.id).all()
        services = []
    
    return render_template('dashboard.html', services=services, requests=requests)