#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESP32Servo.h>
#include "Secrets.h"

// this program runs on ESP32 strapped on rc car
// it receives UDP packets from server
// it reads those packets and translates them into steering and throttle servo signal

const char* serverIp = "192.168.113.244";
//const char* serverIp = "77.240.102.169";
const unsigned int serverPort = 12000;
const unsigned int localUdpPort = 12312; // TODO what is this for?

WiFiUDP udp;

Servo myservo;  // create servo object to control a servo
int servoPin = 13;

void sendInitialUdpPacket() { // this basically connects us to the server so that the server knows where to send all data
  Serial.println("Sending UDP packet...");
  udp.beginPacket(serverIp, serverPort);
  udp.write(0xFF); // Example byte to send
  udp.endPacket();
}

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(",");
  }
  Serial.println("WiFi connected");
  udp.begin(localUdpPort);
  Serial.print("Local UDP port: ");
  Serial.println(localUdpPort);
  
  pinMode(2, OUTPUT);

  ESP32PWM::allocateTimer(0);
	myservo.setPeriodHertz(50);    // standard 50 hz servo
	myservo.attach(servoPin, 500, 2200); // attaches the servo on pin 18 to the servo object

  sendInitialUdpPacket();
}

byte b = 0;

void loop() {
  char incomingPacket[255]; 
  int packetSize = udp.parsePacket();
  if (packetSize) {
    //Serial.printf("Got packet!");
    int len = udp.read(incomingPacket, 255);
    if (len >= 5 && incomingPacket[0] == 255 && incomingPacket[4] == 0) {
      if (incomingPacket[1] == 1) { // steering & throttle packet
        Serial.printf("Steering is %3d, throttle is %3d\n", incomingPacket[2], incomingPacket[3]);
        int mapped = map(incomingPacket[1], 1, 255, 180, 0);
        myservo.write(mapped);
      } else if (incomingPacket[1] == 3)
      {
        // TODO pong
      } else {
        Serial.printf("Got unknown packet");
      }
      //Serial.printf(" Throttle is %3d\n", incomingPacket[2]);
    } else {
      Serial.printf("But it's len is not 5 (%d) or header is not 0xFF(%d) or tail is not 0x00 (%d)", len, incomingPacket[0], incomingPacket[4]);
    }
  }
  delay(5);
}