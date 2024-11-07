from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app import app, db
from models import User, Service, ServiceRequest, Rating, ServiceTag, ServiceCategory
from urllib.parse import urlparse
import re
import os
import json
from datetime import datetime
from PIL import Image
from functools import wraps

def provider_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_provider:
            flash('Access denied. Provider privileges required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_IMAGE_EXTENSIONS']

def save_image(file, folder):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], folder, filename)
        
        # Save and optimize image
        img = Image.open(file)
        img.thumbnail((800, 800))  # Resize if too large
        img.save(filepath, optimize=True, quality=85)
        
        return os.path.join(folder, filename)
    return None

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

@app.route('/')
def index():
    return redirect(url_for('service_list'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please fill in all fields', 'danger')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(password):
            flash('Invalid email or password', 'danger')
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
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        is_provider = request.form.get('is_provider') == 'on'
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        
        if not all([username, email, password, latitude, longitude]):
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('register'))
        
        if not re.match(r'^[A-Za-z0-9_]{3,20}$', username):
            flash('Username must be 3-20 characters long and contain only letters, numbers, and underscores', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        if not validate_password(password):
            flash('Password must be at least 8 characters long and include uppercase, lowercase, and numbers', 'danger')
            return redirect(url_for('register'))
        
        try:
            user = User(
                username=username,
                email=email,
                is_provider=is_provider,
                latitude=float(latitude),
                longitude=float(longitude)
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except ValueError:
            flash('Invalid location coordinates', 'danger')
            return redirect(url_for('register'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
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

@app.route('/service/add', methods=['GET', 'POST'])
@login_required
@provider_required
def add_service():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        detailed_description = request.form.get('detailed_description')
        rate = request.form.get('rate')
        project_rate = request.form.get('project_rate')
        category_id = request.form.get('category_id')
        tag_names = request.form.getlist('tags')
        availability = request.form.get('availability')
        
        if not all([title, description, rate, category_id]):
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('add_service'))
        
        try:
            # Handle portfolio images
            portfolio_images = []
            for file in request.files.getlist('portfolio_images'):
                if file:
                    filepath = save_image(file, 'portfolio')
                    if filepath:
                        portfolio_images.append(filepath)

            # Process tags
            tags = []
            for tag_name in tag_names:
                tag = ServiceTag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = ServiceTag(name=tag_name)
                    db.session.add(tag)
                tags.append(tag)

            service = Service(
                title=title,
                description=description,
                detailed_description=detailed_description,
                rate=float(rate),
                project_rate=float(project_rate) if project_rate else None,
                provider_id=current_user.id,
                category_id=category_id,
                portfolio_images=portfolio_images,
                availability=json.loads(availability) if availability else None,
                tags=tags
            )
            db.session.add(service)
            db.session.commit()
            flash('Service added successfully!', 'success')
            return redirect(url_for('dashboard'))
        except ValueError:
            flash('Invalid rate value', 'danger')
            return redirect(url_for('add_service'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while adding the service. Please try again.', 'danger')
            return redirect(url_for('add_service'))
    
    # Get all main categories with their subcategories
    categories = ServiceCategory.query.filter_by(parent_id=None).all()
    tags = ServiceTag.query.all()
    return render_template('provider_service_add.html', categories=categories, tags=tags)

@app.route('/service/edit/<int:service_id>', methods=['GET', 'POST'])
@login_required
@provider_required
def edit_service(service_id):
    service = Service.query.get_or_404(service_id)
    if service.provider_id != current_user.id:
        flash('You can only edit your own services', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        detailed_description = request.form.get('detailed_description')
        rate = request.form.get('rate')
        project_rate = request.form.get('project_rate')
        category_id = request.form.get('category_id')
        tag_names = request.form.getlist('tags')
        availability = request.form.get('availability')
        remove_images = request.form.getlist('remove_images')
        
        if not all([title, description, rate, category_id]):
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('edit_service', service_id=service_id))
        
        try:
            # Update basic information
            service.title = title
            service.description = description
            service.detailed_description = detailed_description
            service.rate = float(rate)
            service.project_rate = float(project_rate) if project_rate else None
            service.category_id = category_id
            
            # Update availability
            if availability:
                service.availability = json.loads(availability)
            
            # Handle portfolio images
            portfolio_images = list(service.portfolio_images or [])
            # Remove selected images
            for image in remove_images:
                if image in portfolio_images:
                    portfolio_images.remove(image)
                    # Delete the file
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image)
                    if os.path.exists(file_path):
                        os.remove(file_path)
            
            # Add new images
            for file in request.files.getlist('portfolio_images'):
                if file:
                    filepath = save_image(file, 'portfolio')
                    if filepath:
                        portfolio_images.append(filepath)
            
            service.portfolio_images = portfolio_images

            # Update tags
            service.tags = []
            for tag_name in tag_names:
                tag = ServiceTag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = ServiceTag(name=tag_name)
                    db.session.add(tag)
                service.tags.append(tag)
            
            db.session.commit()
            flash('Service updated successfully!', 'success')
            return redirect(url_for('dashboard'))
        except ValueError:
            flash('Invalid rate value', 'danger')
            return redirect(url_for('edit_service', service_id=service_id))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the service. Please try again.', 'danger')
            return redirect(url_for('edit_service', service_id=service_id))
    
    # Get all main categories with their subcategories and tags for the form
    categories = ServiceCategory.query.filter_by(parent_id=None).all()
    tags = ServiceTag.query.all()
    return render_template('provider_service_edit.html', service=service, categories=categories, tags=tags)

@app.route('/service/delete/<int:service_id>', methods=['POST'])
@login_required
@provider_required
def delete_service(service_id):
    service = Service.query.get_or_404(service_id)
    if service.provider_id != current_user.id:
        flash('You can only delete your own services', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        db.session.delete(service)
        db.session.commit()
        flash('Service deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the service. Please try again.', 'danger')
    
    return redirect(url_for('dashboard'))

@app.route('/service/request/<int:service_id>', methods=['POST'])
@login_required
def request_service(service_id):
    service = Service.query.get_or_404(service_id)
    if service.provider_id == current_user.id:
        flash('You cannot request your own service', 'danger')
        return redirect(url_for('service_detail', id=service_id))
    
    request = ServiceRequest(service_id=service_id, client_id=current_user.id)
    db.session.add(request)
    db.session.commit()
    flash('Service requested successfully', 'success')
    return redirect(url_for('service_detail', id=service_id))

@app.route('/service/request/<int:request_id>/status/<status>', methods=['POST'])
@login_required
@provider_required
def update_request_status(request_id, status):
    if status not in ['accepted', 'declined']:
        flash('Invalid status', 'danger')
        return redirect(url_for('dashboard'))
    
    service_request = ServiceRequest.query.get_or_404(request_id)
    if service_request.service.provider_id != current_user.id:
        flash('You can only update status for your own service requests', 'danger')
        return redirect(url_for('dashboard'))
    
    service_request.status = status
    db.session.commit()
    flash(f'Request {status} successfully', 'success')
    return redirect(url_for('dashboard'))

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

@app.route('/update_profile_image', methods=['POST'])
@login_required
def update_profile_image():
    if 'profile_image' not in request.files:
        flash('No file provided', 'danger')
        return redirect(url_for('dashboard'))
    
    file = request.files['profile_image']
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        filepath = save_image(file, 'profiles')
        if filepath:
            if current_user.profile_image:
                # Delete old profile image
                old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.profile_image)
                if os.path.exists(old_path):
                    os.remove(old_path)
            
            current_user.profile_image = filepath
            db.session.commit()
            flash('Profile image updated successfully!', 'success')
        else:
            flash('Invalid file type', 'danger')
    except Exception as e:
        db.session.rollback()
        flash('Error updating profile image', 'danger')
    
    return redirect(url_for('dashboard'))