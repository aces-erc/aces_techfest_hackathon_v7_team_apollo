#include <WiFi.h>
#include <PubSubClient.h>

// WiFi credentials
const char* ssid = "NB_A";
const char* password = "12345Niraj";

// MQTT broker details
const char* mqtt_server = "192.168.137.225";
const int mqtt_port = 1883;
const char* ultrasonic_topic = "ultrasonic/distance";
const char* air_quality_topic = "air_quality/status";

// Ultrasonic sensor pins
const int trigPin = 4;  // GPIO5
const int echoPin = 2; // GPIO18

// MQ-135 sensor pin
const int MQ135_PIN = 34; // GPIO34 (ADC1_CH6)

// ADC configuration
const float ADC_VREF = 3.3;
const float ADC_RESOLUTION = 4095.0;

WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
  Serial.begin(115200);
  
  // Initialize sensor pins
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(MQ135_PIN, INPUT);
  
  // Configure ADC
  analogSetWidth(12);
  analogSetAttenuation(ADC_11db);
  
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
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

float readDistance() {
  // Trigger ultrasonic measurement
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  // Read the echo pulse
  long duration = pulseIn(echoPin, HIGH);
  float distance = duration * 0.034 / 2;
  
  return distance;
}

String readAirQuality() {
  // Read sensor with averaging
  int sensorValue = 0;
  for(int i = 0; i < 10; i++) {
    sensorValue += analogRead(MQ135_PIN);
    delay(10);
  }
  sensorValue = sensorValue / 10;
  
  // Convert to voltage
  float voltage = (sensorValue * ADC_VREF) / ADC_RESOLUTION;
  float ppm = map(sensorValue, 0, 4095, 400, 10000);

  // Determine air quality level
  String airQuality;
  if (ppm <= 400) {
    airQuality = "Very Good";
  } else if (ppm <= 1000) {
    airQuality = "Good";
  } else if (ppm <= 2000) {
    airQuality = "Moderate";
  } else if (ppm <= 5000) {
    airQuality = "Bad";
  } else {
    airQuality = "Very Bad";
  }

  Serial.printf("Air Quality Raw: %d, Voltage: %.2fV, PPM: %.0f, Status: %s\n", 
                sensorValue, voltage, ppm, airQuality.c_str());
                
  return airQuality;
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("ESP32Client")) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Read sensors
  float distance = readDistance();
  String airQuality = readAirQuality();

  // Convert distance to string
  char distanceStr[8];
  dtostrf(distance, 1, 2, distanceStr);

  // Publish data
  client.publish(ultrasonic_topic, distanceStr);
  client.publish(air_quality_topic, airQuality.c_str());

  // Debug output
  Serial.printf("Distance: %.2f cm\n", distance);

  delay(2000);
}