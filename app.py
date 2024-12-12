from flask import Flask, render_template, jsonify, redirect, url_for
import paho.mqtt.client as mqtt
from datetime import datetime
from twilio.rest import Client
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

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

@app.route('/')
def index():
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
        'emergency.html',
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

if __name__ == "__main__":
    socketio.run(app, debug=True)