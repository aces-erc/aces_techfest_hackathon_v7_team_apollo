from flask import Flask, render_template, request
import paho.mqtt.client as mqtt

app = Flask(__name__)

# MQTT setup
mqtt_broker = "192.168.1.227"  # Replace with your MQTT broker address
mqtt_port = 1883
mqtt_topic = "crashDetection"
distance_topic = "ultrasonic/distance"
emergency_topic = "emergency/signal"

client = mqtt.Client()

# Connect to the MQTT broker
try:
    client.connect(mqtt_broker, mqtt_port, 60)
except Exception as e:
    print(f"Failed to connect to MQTT broker: {e}")

# Define the on_message callback
def on_message(client, userdata, msg):
    if msg.topic == distance_topic:
        try:
            distance = float(msg.payload.decode())
            if distance < 10:
                print("Crash detected! Dispatching emergency signal.")
                client.publish(emergency_topic, "CRASH DETECTED")
        except ValueError:
            print("Error: Invalid distance value received")

# Set the on_message callback
client.on_message = on_message

# Subscribe to the distance topic
client.subscribe(distance_topic)

# Start the MQTT client loop
client.loop_start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/led/<action>')
def led_control(action):
    if action == "on":
        client.publish(mqtt_topic, "ON")
    elif action == "off":
        client.publish(mqtt_topic, "OFF")
    return f"LED turned {action}"

if __name__ == '__main__':
    app.run(debug=True)