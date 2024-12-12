from flask import Flask, render_template, jsonify, redirect, url_for, flash, session, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
import paho.mqtt.client as mqtt
from datetime import datetime
from twilio.rest import Client
from flask_socketio import SocketIO, emit
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeSerializer

app = Flask(__name__)
socketio = SocketIO(app)



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


# MQTT setup
MQTT_BROKER = "192.168.137.217"
MQTT_PORT = 1883
ULTRASONIC_TOPIC = "ultrasonic/distance"
AIR_QUALITY_TOPIC = "air_quality/status"
BUTTON_EMERGENCY = "button/emergency"
EMERGENCY_SIGNAL = "emergency/signal"

client = mqtt.Client()

# Twilio account credentials
account_sid = 'ACa72adc5cdd59a11f2aa935f3c4ec5509'
auth_token = 'b1fc212c56363e91d0d6b996c3cacd1a'
twilio_client = Client(account_sid, auth_token)

# Phone numbers
to_number = '+9779807941286'  # The number you want to call
from_number = '+13204349487'  # Your verified or purchased Twilio phone number

# Global variables
distance_data = None
air_quality_status = None
mqtt_connected = False
emergency_triggered = False  # Flag for emergency
data = 'None'
trigger_type = 'None'
button_emergency = False

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_connected = True
except Exception as e:
    print(f"Failed to connect to MQTT broker: {e}")

def on_message(client, userdata, msg):
    global distance_data, air_quality_status, emergency_triggered, button_emergency
    print(f"MQTT Message received: {msg.topic} {msg.payload.decode()}")

    try:
        if msg.topic == ULTRASONIC_TOPIC:
            distance_data = float(msg.payload.decode())
            print(f"Updated distance: {distance_data} cm")
            if distance_data < 10:
                emergency_triggered = True
                print("Emergency Signal Triggered!")
                socketio.emit('emergency_signal', {'message': 'Emergency Signal Triggered!'})
            else:
                emergency_triggered = False
            socketio.emit('distance_update', {'distance': distance_data})

        if msg.topic == AIR_QUALITY_TOPIC:
            air_quality_status = msg.payload.decode()
            print(f"Updated air quality: {air_quality_status}")
            socketio.emit('air_quality_update', {'status': air_quality_status})

        if msg.topic == BUTTON_EMERGENCY:
            print("Emergency Signal Triggered!")
            button_emergency = True
            socketio.emit('emergency_signal', {'message': 'Button Emergency Triggered!'})
        else:
            button_emergency = False
    except ValueError as e:
        print(f"Error processing message: {e}")

def trigger_phone_call():
    call = twilio_client.calls.create(
        twiml='<Response><Say>Emergency detected! Please take action immediately.</Say></Response>',
        to=to_number,
        from_=from_number
    )
    print(f"Call initiated with SID: {call.sid}")

client.on_message = on_message
client.subscribe(ULTRASONIC_TOPIC)
client.subscribe(EMERGENCY_SIGNAL)
client.subscribe(AIR_QUALITY_TOPIC)
client.subscribe(BUTTON_EMERGENCY)

client.loop_start()

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
def index():
    if "username" in session:
        return render_template('dashboard.html', username = session['username'])
    else:
        global distance_data, air_quality_status, mqtt_connected, emergency_triggered, button_emergency
        if emergency_triggered or button_emergency:
            return redirect('/emergency')
        return render_template(
			'index.html',
			distance=distance_data,
			emergency_triggered=emergency_triggered,
			button_emergency = button_emergency,
			air_quality=air_quality_status,
			mqtt_connected=mqtt_connected,
		)

@app.route('/emergency')
def emergency():
    global emergency_triggered, distance_data, data, trigger_type, button_emergency
    if distance_data is not None and int(distance_data) >= 10:  # Check if distance is no longer critical
        emergency_triggered = False
    if button_emergency:
        trigger_type = "Button Emergency"
        data = "Emergency triggered by pressing the button!"
    elif emergency_triggered:
        trigger_type = "Ultrasonic Emergency"
        data = "Emergency triggered by ultrasonic sensor!"
    else:
        trigger_type = "None"
        data = "No emergency at the moment."

    return render_template(
        '/logged_id/emergency.html',
        button_emergency=button_emergency,
        emergency_triggered=emergency_triggered,
        trigger_type=trigger_type,
        data=data,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

@app.route('/status')
def status():
    return jsonify({
        'mqtt_connected': mqtt_connected,
        'distance': distance_data,
        'emergency': emergency_triggered,
        'air_quality': air_quality_status,
        'button_emergency': button_emergency
    })

@app.route('/trigger_call')
def trigger_call():
    trigger_phone_call()
    return redirect(url_for('emergency'))

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

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)
