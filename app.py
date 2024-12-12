from flask import Flask, render_template, jsonify, redirect
import paho.mqtt.client as mqtt

app = Flask(__name__)

# MQTT setup
MQTT_BROKER = "192.168.137.225"
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

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
except Exception as e:
    print(f"Failed to connect to MQTT broker: {e}")


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

        if msg.topic == AIR_QUALITY_TOPIC:
            air_quality_status = msg.payload.decode()
            print(f"Updated air quality: {air_quality_status}")
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
    return render_template(
        'index.html',
        distance=distance_data,
        emergency_triggered=emergency_triggered,
        air_quality=air_quality_status,
        mqtt_connected=mqtt_connected
    )


@app.route('/emergency')
def emergency():
    global distance_data
    return render_template('emergency.html', distance=distance_data)


@app.route('/status')
def status():
    return jsonify({
        'mqtt_connected': mqtt_connected,
        'distance': distance_data,
        'emergency': emergency_triggered,
        'air_quality': air_quality_status
    })


if __name__ == "__main__":
    app.run(debug=True)
