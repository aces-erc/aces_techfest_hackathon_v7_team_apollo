#include <WiFi.h>
#include <PubSubClient.h>

// WiFi credentials
const char* ssid = "NB_A";
const char* password = "12345Niraj";

// MQTT broker details
const char* mqtt_server = "192.168.137.217";  // Replace with your MQTT broker address
const int mqtt_port = 1883;
const char* distance_topic = "ultrasonic/distance";
const char* emergency_topic = "emergency/signal";
const char* button_topic = "button/emergency";

// Ultrasonic sensor pins
const int trigPin = 12;
const int echoPin = 14;

// Button and LED pins for emergency signal
const int buttonPin = 26; // GPIO pin for the push button
const int ledPin = 2;   // GPIO pin for the emergency signal (LED)

// Initialize WiFi and MQTT clients
WiFiClient espClient;
PubSubClient client(espClient);

// Variables to track the button state
bool buttonPressed = false;
unsigned long buttonPressStart = 0;

void setup() {
  Serial.begin(115200);

  // Set up ultrasonic sensor pins
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  // Set up button and LED pins
  pinMode(buttonPin, INPUT_PULLUP); // Configure button pin as input with pull-up resistor
  pinMode(ledPin, OUTPUT);          // Configure LED pin as output

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

  // Convert distance to string and publish to MQTT
  String disp = String(distance);
  Serial.println(distance);  // Print distance to serial monitor

  char distanceStr[8];
  dtostrf(distance, 1, 2, distanceStr);
  client.publish(distance_topic, distanceStr);

  // Read the button state (LOW when pressed, HIGH when released due to pull-up)
  bool buttonState = digitalRead(buttonPin) == LOW;

  if (buttonState && !buttonPressed) {
    // Button is just pressed
    buttonPressed = true;
    buttonPressStart = millis(); // Record the time when the button was pressed
  } else if (!buttonState && buttonPressed) {
    // Button is released
    buttonPressed = false;
  }

  // Check if the button has been held for 5 seconds
  if (buttonPressed && millis() - buttonPressStart >= 5000) {
    // Emergency signal triggered
    Serial.println("Emergency signal generated!");
    digitalWrite(ledPin, HIGH); // Turn on the LED to indicate the signal

    // Send emergency signal to MQTT
    client.publish(button_topic, "Emergency signal triggered!");

    // Hold the signal for demonstration
    delay(2000);               // Keep the signal on for 2 seconds
    digitalWrite(ledPin, LOW); // Turn off the LED

    // Reset state
    buttonPressed = false;
  }

  delay(1000);  // Wait for a second before next measurement and loop iteration
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
