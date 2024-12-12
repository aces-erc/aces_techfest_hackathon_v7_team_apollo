#include <WiFi.h>
#include <PubSubClient.h>

// WiFi credentials
const char* ssid = "NB_A";
const char* password = "12345Niraj";

// MQTT broker details
const char* mqtt_server = "192.168.137.71";  // Replace with your MQTT broker address
const int mqtt_port = 1883;
const char* distance_topic = "ultrasonic/distance";

// Ultrasonic sensor pins
const int trigPin = 4;
const int echoPin = 2;

// Initialize WiFi and MQTT clients
WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
  Serial.begin(115200);
  
  // Set up ultrasonic sensor pins
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  // Connect to WiFi
  setup_wifi();

  // Set up MQTT server
  client.setServer(mqtt_server, mqtt_port);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Measure distance
  long duration, distance;
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  duration = pulseIn(echoPin, HIGH);
  distance = (duration / 58.2);

  String disp = String(distance);
  Serial.println(distance);  // Convert to cm

  // Publish distance to MQTT broker
  char distanceStr[8];
  dtostrf(distance, 1, 2, distanceStr);
  client.publish(distance_topic, distanceStr);

  delay(1000);  // Wait for a second before next measurement
}

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("ESP32Client")) {  // Use a unique client ID
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}