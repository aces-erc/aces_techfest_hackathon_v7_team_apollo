#include <Wire.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// Define pins
#define echoPin 2
#define trigPin 4

// WiFi credentials
const char* ssid = "Hackthon_Worldlink";
const char* password = "AcesHackathon@123";

// MQTT broker settings
const char* mqttServer = "192.168.1.226";
const int mqttPort = 1883;
const char* mqttTopic = "crashDetection";

// MQTT client
WiFiClient espClient;
PubSubClient client(espClient);

long duration, distance;

void setup() {
  // Start serial communication
  Serial.begin(115200);

  // Set pin modes
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  // Connect to WiFi
  setupWiFi();

  // Set MQTT server
  client.setServer(mqttServer, mqttPort);
}

void loop() {
  // Reconnect to MQTT if needed
  if (!client.connected()) {
    reconnectMQTT();
  }

  client.loop();  // Keep MQTT connection alive

  // Measure distance
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  duration = pulseIn(echoPin, HIGH);
  distance = duration / 58.2;

  // If the distance is below 4 cm, send a "Crash Detected" message
  if (distance < 4) {
    Serial.println("Crash Detected!");
    client.publish(mqttTopic, "Crash Detected");
  }

  // Print distance for debugging
  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.println(" cm");

  delay(1000);  // Wait for a second before next reading
}

void setupWiFi() {
  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("Connected to WiFi");
}

void reconnectMQTT() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Connecting to MQTT...");
    
    // Attempt to connect
    if (client.connect("CrashDetectorClient", mqttUser, mqttPassword)) {
      Serial.println("Connected to MQTT");
      // Subscribe to a topic (optional)
      // client.subscribe("your_subscribe_topic");
    } else {
      Serial.print("Failed to connect to MQTT, rc=");
      Serial.print(client.state());
      delay(5000);  // Wait before retrying
    }
  }
}
