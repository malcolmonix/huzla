from flask import render_template, redirect, url_for, flash, request, jsonify, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from app import app, db
from models import User, Service, ServiceRequest, Rating, ServiceTag, ServiceCategory
from urllib.parse import urlparse, urlencode
import re
import os
import json
from datetime import datetime
from PIL import Image
from functools import wraps
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import WebApplicationClient
import requests

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

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

@app.route("/login/google")
def login_google():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@app.route("/login/google/callback")
def callback_google():
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    if not code:
        flash("Authentication failed", "danger")
        return redirect(url_for("login"))

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send request to get tokens
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that we have tokens, let's find and hit URL
    # from Google that gives you user's profile information,
    # including their Google Profile Image and Email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    if userinfo_response.json().get("email_verified"):
        google_id = userinfo_response.json()["sub"]
        email = userinfo_response.json()["email"]
        name = userinfo_response.json()["given_name"]

        # Check if user exists
        user = User.query.filter_by(google_id=google_id).first()
        if not user:
            # Check if email exists
            user = User.query.filter_by(email=email).first()
            if user:
                # Link existing account with Google
                user.google_id = google_id
                user.is_google_auth = True
                db.session.commit()
            else:
                # Create new user
                user = User(
                    username=name,
                    email=email,
                    google_id=google_id,
                    is_google_auth=True
                )
                db.session.add(user)
                db.session.commit()

        login_user(user)
        flash('Logged in successfully via Google!', 'success')
        return redirect(url_for('index'))
    else:
        flash("Google authentication failed", "danger")
        return redirect(url_for("login"))

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

# ... [rest of the routes from the previous version] ...
