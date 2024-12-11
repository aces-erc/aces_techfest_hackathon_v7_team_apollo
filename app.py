from flask import Flask, render_template, request
import paho.mqtt.client as mqtt

app = Flask(__name__)

# MQTT setup
mqtt_broker = "192.168.1.226"  # Replace with your MQTT broker address
mqtt_port = 1883
mqtt_topic = "crashDetection"

client = mqtt.Client()
client.connect(mqtt_broker, mqtt_port, 60)

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