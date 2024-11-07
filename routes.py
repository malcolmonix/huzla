from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Service, ServiceRequest, Rating
from urllib.parse import urlparse

@app.route('/')
def index():
    return redirect(url_for('service_list'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user is None or not user.check_password(request.form['password']):
            flash('Invalid email or password')
            return redirect(url_for('login'))
        
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        user = User(
            username=request.form['username'],
            email=request.form['email'],
            is_provider=request.form.get('is_provider') == 'on',
            latitude=float(request.form['latitude']),
            longitude=float(request.form['longitude'])
        )
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        flash('Registration successful!')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
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
