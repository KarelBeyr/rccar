#include <WiFi.h>
#include <WiFiUdp.h>
#include <ESP32Servo.h>
#include "Secrets.h"

// this program runs on ESP32 strapped on rc car
// it receives UDP packets from server
// it reads those packets and translates them into steering and throttle servo signal

//const char* serverIp = "192.168.113.211"; // ntb
//const char* serverIp = "192.168.113.244"; // raspi
const char* serverIp = "77.240.102.169"; // raspi public IP
const unsigned int serverPort = 12000;
const unsigned int localUdpPort = 12312; // is not important

WiFiUDP udp;

Servo steeringServo;
int steeringServoPin = 13;
Servo throttleServo;
int throttleServoPin = 27;
int throttleInputPin = 12;
int steeringInputPin = 14;

void sendInitialUdpPacket() { // this basically connects us to the server so that the server knows where to send all data. Also serves as keep-alive packet for all NAT entries on the way.
  Serial.print("H");
  udp.beginPacket(serverIp, serverPort);
  udp.write(42); // Random byte to send
  udp.endPacket();
}

uint32_t lastTxPacketMillis = 0;
long lastThrMicros;
long currentThrDelta;
void throttleInputIntHandler()
{
  long currentMicros = micros();
  long delta = currentMicros - lastThrMicros;
  if (delta < 2000) currentThrDelta = delta;
  lastThrMicros = currentMicros;
  lastTxPacketMillis = millis();
}

long lastSteerMicros;
long currentSteerDelta;
void steeringInputIntHandler()
{
  long currentMicros = micros();
  long delta = currentMicros - lastSteerMicros;
  if (delta < 2000) currentSteerDelta = delta;
  lastSteerMicros = currentMicros;
  lastTxPacketMillis = millis();
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
	steeringServo.setPeriodHertz(50);    // TRX-4 uses standard 50 hz servo
	steeringServo.attach(steeringServoPin, 1040, 2000); // 1040, 2000 were empirically found to be "compatible" with TRX-4 receiver so that they have the same endpoints and same midpoint
	throttleServo.setPeriodHertz(50);
	throttleServo.attach(throttleServoPin, 1040, 2000);

  pinMode(throttleInputPin, INPUT_PULLUP);

  
  delay(500); // Some Delay 1. before attaching interrupts 2. for millis() to be reasonable far from initial value of lastTxPacketMillis
  attachInterrupt(digitalPinToInterrupt(throttleInputPin), throttleInputIntHandler, CHANGE);
  attachInterrupt(digitalPinToInterrupt(steeringInputPin), steeringInputIntHandler, CHANGE);
}

long lastSec = -1;

void controlServos(char steering, char throttle) {
  Serial.printf("Steering is %3d, throttle is %3d\n", steering, throttle);
  steeringServo.write(map(steering, 1, 254, 180, 0));
  throttleServo.write(map(throttle, 1, 254, 180, 0));
}

void loop() {
  long currentSec = millis() / 200; // I want to send heartbeat packet every 5 seconds
  if (currentSec > lastSec) {
    lastSec = currentSec;
    sendInitialUdpPacket();
  }

  bool servosServed = false;
  char txthr = map(currentThrDelta, 1000, 2000, 254, 1);
  char txsteer = map(currentSteerDelta, 1000, 2000, 254, 1);

  if ((millis() - lastTxPacketMillis) < 500) { // if we received last packet from TX "recently"
    Serial.println("Got recent TX packet");
    if (txthr < 118 || txthr > 138 || txsteer < 118 || txsteer > 138) { // if TX is sending some non-central value
      controlServos(txsteer, txthr);
      servosServed = true;
    }
  }

  char incomingPacket[255]; 
  int packetSize = udp.parsePacket();
  if (packetSize) {
    //Serial.printf("Got packet!");
    int len = udp.read(incomingPacket, 255);
    if (len >= 5 && incomingPacket[0] == 255 && incomingPacket[4] == 0) {
      if (incomingPacket[1] == 1) { // steering & throttle packet
        if (!servosServed) {
          char steering = incomingPacket[2];
          char throttle = incomingPacket[3];
          controlServos(steering, throttle);
        }
      } else if (incomingPacket[1] == 3)
      {
        char pongPacket[] = {0xFF, 0x03, txthr, txsteer, 0x00}; // Type 3 for pong
        udp.beginPacket(serverIp, serverPort);
        udp.write((unsigned char*)pongPacket, sizeof(pongPacket));
        udp.endPacket();
        Serial.printf("Sent pong packet");
      } else {
        Serial.printf("Got unknown packet");
      }
    } else {
      Serial.printf("Malformed packet: len is not 5 (%d) or header is not 0xFF(%d) or tail is not 0x00 (%d)", len, incomingPacket[0], incomingPacket[4]);
    }
  }
}