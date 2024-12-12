from flask import Flask, render_template, jsonify, redirect
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app)

# MQTT setup
MQTT_BROKER = "192.168.137.71"
MQTT_PORT = 1883
ULTRASONIC_TOPIC = "ultrasonic/distance"
AIR_QUALITY_TOPIC = "air_quality/status"
EMERGENCY_SIGNAL = "emergency/signal"

client = mqtt.Client()

# Global variables
distance_data = None
air_quality_status = None
mqtt_connected = False
emergency_triggered = False  # Flag for emergency

# Attempt to connect to MQTT broker
try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_connected = True
except Exception as e:
    print(f"Failed to connect to MQTT broker: {e}")

# MQTT message handling
def on_message(client, userdata, msg):
    global distance_data, air_quality_status, emergency_triggered
    print(f"MQTT Message received: {msg.topic} {msg.payload.decode()}")

    try:
        if msg.topic == ULTRASONIC_TOPIC:
            distance_data = float(msg.payload.decode())
            print(f"Updated distance: {distance_data} cm")
            if distance_data < 10:
                emergency_triggered = True
                print("Emergency Signal Triggered!")
                # Notify clients in real time
                socketio.emit('emergency_signal', {'message': 'Emergency Triggered!', 'distance': distance_data})
            else:
                emergency_triggered = False
            socketio.emit('distance_update', {'distance': distance_data})

        if msg.topic == AIR_QUALITY_TOPIC:
            air_quality_status = msg.payload.decode()
            print(f"Updated air quality: {air_quality_status}")
            # Notify clients of air quality updates
            socketio.emit('air_quality_update', {'status': air_quality_status})
    except ValueError as e:
        print(f"Error processing message: {e}")

client.on_message = on_message
client.subscribe(ULTRASONIC_TOPIC)
client.subscribe(EMERGENCY_SIGNAL)
client.subscribe(AIR_QUALITY_TOPIC)
client.loop_start()

@app.route('/')
def index():
    global distance_data, air_quality_status, mqtt_connected, emergency_triggered
    if emergency_triggered:
        return redirect('/emergency')
    return render_template(
        'index.html',
        distance=distance_data,
        air_quality=air_quality_status,
        mqtt_connected=mqtt_connected
    )

@app.route('/emergency')
def emergency():
    global emergency_triggered, distance_data
    if distance_data is not None and int(distance_data) >= 10:  # Check if distance is no longer critical
        emergency_triggered = False
    return render_template('emergency.html', 
        trigger_type="Distance Alert",
        data=f"Critical Distance Detected: {distance_data} cm",
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

@app.route('/status')
def status():
    return jsonify({
        'mqtt_connected': mqtt_connected,
        'distance': distance_data,
        'emergency': emergency_triggered,
        'air_quality': air_quality_status
    })

# Handle Socket.IO client connection
@socketio.on('connect')
def connect():
    global distance_data, air_quality_status, mqtt_connected, emergency_triggered
    emit('distance_update', {'distance': distance_data})
    emit('air_quality_update', {'status': air_quality_status})
    emit('emergency_update', {'emergency': emergency_triggered})

if __name__ == "__main__":
    socketio.run(app, debug=True)
