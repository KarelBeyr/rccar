#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESP32Servo.h>
#include "Secrets.h"

// this program runs on ESP32 strapped on rc car
// it receives UDP packets from server
// it reads those packets and translates them into steering and throttle servo signal

//const char* serverIp = "192.168.113.244";
const char* serverIp = "77.240.102.169";
const unsigned int serverPort = 12000;
const unsigned int localUdpPort = 12312; // TODO what is this for?

WiFiUDP udp;

Servo myservo;  // create servo object to control a servo
int servoPin = 13;

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected");
  udp.begin(localUdpPort);
  Serial.print("Local UDP port: ");
  Serial.println(localUdpPort);
  pinMode(2, OUTPUT);

  ESP32PWM::allocateTimer(0);
	myservo.setPeriodHertz(50);    // standard 50 hz servo
	myservo.attach(servoPin, 500, 2200); // attaches the servo on pin 18 to the servo object
}

byte b = 0;

void loop() {
  Serial.printf(".");
  udp.beginPacket(serverIp, serverPort);
  udp.write(b++);
  udp.endPacket();

  char incomingPacket[255]; 
  int packetSize = udp.parsePacket();
  if (packetSize) {
    //Serial.printf("Got packet!");
    int len = udp.read(incomingPacket, 255);
    if (len > 0) {
      //Serial.printf("len is %i", len);
      incomingPacket[len] = 0;
      // if (incomingPacket[0] == 255) Serial.printf("OK: First byte is 255");
      // if (incomingPacket[4] == 0) Serial.printf("OK: Fourth byte is 0");
      Serial.printf("Steering is %3d, throttle is %3d\n", incomingPacket[1], incomingPacket[2]);
      int mapped = map(incomingPacket[1], 1, 255, 180, 0);
      myservo.write(mapped);
      //Serial.printf(" Throttle is %3d\n", incomingPacket[2]);
    } else {
      Serial.printf("But it's len is 0");
    }
    //Serial.printf("Received reply: %s\n", incomingPacket);
  }
  delay(25);
}