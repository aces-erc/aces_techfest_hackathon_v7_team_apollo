from flask import Flask, render_template
import paho.mqtt.client as mqtt

app = Flask(__name__)

# MQTT configuration
MQTT_BROKER = "192.168.137.227"  # Replace with your broker address
MQTT_PORT = 1883
MQTT_TOPIC = "ultrasonic/distance"

client = mqtt.Client()

# Global variable to hold the distance value
distance_data = None

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
except Exception as e:
    print(f"Failed to connect to MQTT broker: {e}")

# Function to handle MQTT messages
def on_message(client, userdata, msg):
    global distance_data
    print(f"MQTT Message Received.")
    try:
        distance_data = float(msg.payload.decode())
        print(f"Received distance: {distance_data} cm")
    except ValueError:
        print("Invalid distance data received")

client.on_message = on_message

client.subscribe(MQTT_TOPIC)

client.loop_start()

# Flask route to display the data
@app.route('/')
def index():
    global distance_data
    emergency = distance_data is not None and distance_data < 10  # Check if distance is below 10 cm
    return render_template('index.html', distance=distance_data, emergency=emergency)

if __name__ == "__main__":
    # Start the Flask app
    app.run(debug=True)
