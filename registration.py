from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_mail import Mail, Message
import secrets
import os
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "Hello"

# Configure SQL Alchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'abhisekniraula321@gmail.com'  # Website email , from this i can send
app.config['MAIL_PASSWORD'] = 'gmrz opcb kyxd cgys'  # Website email app password
ADMIN_EMAIL = '080bei004@ioepc.edu.np'  # Admin receiving verification emails

db = SQLAlchemy(app)
mail = Mail(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25),unique=True, nullable=False)
    # email = db.Column(db.String(100), unique=True , nullable=False)
    password_hash = db.Column(db.String(200))  # Rename column to password_hash

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Update AdminVerification model
class AdminVerification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True)
    email = db.Column(db.String(120), unique=True) 
    password_hash = db.Column(db.String(200))
    verification_token = db.Column(db.String(100), unique=True)
    token_expiry = db.Column(db.DateTime)  # Make sure this column exists
    is_verified = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
@app.route('/')
def home():
    if "username" in session:
        return render_template('index.html',username=session['username'])
    return render_template('index.html', username='guest')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/sos', methods=['GET', 'POST'])
def sos():
    if request.method == 'POST':
        # Handle SOS action here (e.g., send alert or log data)
        emergency_details = request.form['details']
        return render_template('sos.html', message="SOS Triggered Successfully!")
    return render_template('sos.html')

@app.route('/dashboard')
def dashboard():
    # Simulated hospital data with dynamic percentage calculation
    available_beds_current = 150
    available_beds_total = 200
    available_beds_percentage = (available_beds_current / available_beds_total) * 100
    
    resource_data = {
        'available_beds': {
            'current': available_beds_current,
            'total': available_beds_total,
            'percentage': available_beds_percentage
        },
        'staff_on_duty': {
            'doctors': 45,
            'nurses': 120,
            'total': 165
        },
        'medical_equipment': {
            'ventilators': {
                'available': 30,
                'total': 40,
                'percentage': 75
            },
            'mri_machines': {
                'available': 5,
                'total': 8,
                'percentage': 62.5
            }
        },
        'emergency_room': {
            'current_patients': 25,
            'wait_time': 45,
            'critical_cases': 3
        },
        'patient_statistics': {
            'admissions': 120,
            'discharges': 95,
            'in_patient': 250
        }
    }
    return render_template('dashboard.html', data=resource_data)

#login
@app.route('/login', methods=['GET', 'POST'])
def login():
    session.clear()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if the username is provided
        if not username:
            flash('Username is required.', 'error')
            return redirect(url_for('login'))
        
        # Check if the password is provided
        if not password:
            flash('Password is required.', 'error')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=username).first()
        
        # Check if the user exists
        if not user:
            flash('Invalid username. Please try again.', 'error')
            return redirect(url_for('login'))
        
        # Check if the password is correct
        if user and user.check_password(password):
            session['username'] = username
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password. Please try again.', 'error')
            return redirect(url_for('login'))
    
    return render_template('login.html')
    
# signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'user')
        email = request.form.get('email')

        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose another username.', 'error')
            return redirect(url_for('signup'))

        if role == 'admin':
            try:
                # Check for existing verification
                existing_verify = AdminVerification.query.filter_by(username=username).first()
                if existing_verify:
                    db.session.delete(existing_verify)
                    db.session.commit()

                # Create new verification
                token = secrets.token_urlsafe(32)
                admin_verify = AdminVerification(
                    username=username,
                    verification_token=token
                )
                admin_verify.set_password(password)
                db.session.add(admin_verify)
                
                # Send verification email
                msg = Message('New Admin Verification Request',
                            sender=app.config['MAIL_USERNAME'],
                            recipients=[ADMIN_EMAIL])
                msg.body = f'''
                New admin signup request:
                Username: {username}
                
                To verify this admin request, click here:
                {url_for('verify_admin', token=token, _external=True)}
                '''
                mail.send(msg)
                db.session.commit()
                flash('Admin verification request sent. Please wait for approval.', 'info')
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error in admin verification: {str(e)}', 'error')
                return redirect(url_for('signup'))

        else:
            try:
                # Regular user signup
                user = User(username=username)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                flash('Account created successfully!', 'success')
                return redirect(url_for('login'))
            except IntegrityError:
                db.session.rollback()
                flash('Username already taken. Please choose a different username.', 'error')
            except Exception as e:
                db.session.rollback()
                flash(f'Error creating account: {str(e)}', 'error')

    return render_template('login.html')

def generate_token():
    return secrets.token_urlsafe(32)

@app.route('/admin-signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        # Generate verification token
        token = secrets.token_urlsafe(32)
        expiry = datetime.now() + timedelta(hours=24)
        
        try:
            admin_verify = AdminVerification(
                username=username,
                email=email,
                verification_token=token,
                token_expiry=expiry,
                is_verified=False
            )
            admin_verify.set_password(password)
            
            # Send verification email
            msg = Message('Admin Account Verification',
                        sender=app.config['MAIL_USERNAME'],
                        recipients=[email])
            verification_link = url_for('verify_admin', token=token, _external=True)
            msg.body = f'Click here to verify your admin account: {verification_link}'
            mail.send(msg)
            
            db.session.add(admin_verify)
            db.session.commit()
            
            flash('Please check your email to verify your admin account', 'info')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error in admin verification: {str(e)}', 'error')
            
    return render_template('admin_signup.html')

@app.route('/verify-admin/<token>')
def verify_admin(token):
    admin_verify = AdminVerification.query.filter_by(
        verification_token=token,
        is_verified=False
    ).first()
    
    # Check if admin_verify exists first
    if not admin_verify:
        flash('Invalid verification link', 'error')
        return redirect(url_for('login'))
    
    # Check if token has expired (only if token_expiry exists)
    if admin_verify.token_expiry and admin_verify.token_expiry < datetime.now():
        flash('Verification link has expired', 'error')
        return redirect(url_for('login'))
        
    try:
        # Create verified admin user
        user = User(username=admin_verify.username)
        user.password_hash = admin_verify.password_hash
        
        # Set admin as verified
        admin_verify.is_verified = True
        
        db.session.add(user)
        db.session.commit()
        
        flash('Admin account verified successfully!', 'success')
        return redirect(url_for('login'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error verifying admin account: {str(e)}', 'error')
        
    return redirect(url_for('login'))
   
# Logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))