# RC car forwarding infrastructure
Forwarding signals joystick/controller connected to computer (phone) to ESP32 connected servos in an RC car.

## Current issues
- [ ] security concerns - anybody can currently hijack my car as everything goes unencrypted over public IP address. How to improve? There could be a password field and forwarding server would validate password hash against some hardcoded value..
- [ ] animate input in FE in a better graphical way, ideally show car with turned wheels, but how to display speed?
- [x] enable FE control without having any gamepad connected
- [ ] mirror gamepad input to vjoy visualisation?
- [x] change WS port to 80 or 443 and create cert infra on deployment server. Ideally it should run on http during development and then https during production
- [x] add state button to FE which will show if WS is connected and it will enable it to force connect.
- [ ] why does FE keep sending data all the time, it should only send data if steer or thr differs by two or more..
- [ ] bigger joystick, smaller deadzone (whenever I start using it on the phone, servo jumps a lot)

## Nocode GPT input
### Server component
I want to create a forwarding server that accepts packets from Websocket (from client running in browser and written in Javascript) and forwards those packets to UDP (to client running on ESP32 written in Arduino framework).
- Neither of those clients have static IP address. The server must wait for them to connect actively.
- The server should listen on port 12000 for UDP packets and on port 12001 for websocket packets.
- There are currently three types of packets. The server must not modify those packets and it must understand some of them to react to them accordingly:
   1. Control packet. It has 5 byte structure: First byte is header (0xFF), second byte is type (0x01), third byte is steering, fourth byte is throttle and fifth byte is tail (0x00)
   2. Simple latency packet. It has the same 5 byte structure, except for the second byte which is 0x02. Third and fourth bytes are undefined.
   3. E2E latency packet. It has the same 5 byte structure, except for the third byte which is 0x03. Third and fourth bytes are undefined.
- The server must immediately send response (with the same packet) back to websocket for simple latency packet.
- The server must forward other packets to UDP and in case it receives back some packets from UDP to forward them back into websocket.
- The server must gracefully handle CTR+C to cleanly exit.
- The server needs only to handle a single connection from websocket and a single connection to UDP. However, it must be able to handle both clients to reconnect from new IP address (e.g. websocket or UDP client can restart and they will initiate new websocket or UDP connection).
- The server must be able to accept websocket communication even if UDP is not connected and perform basic tasks (logging incoming packets, replying to latency packet. Of course it would not forward anything).
- The server must be able to accept UDP communication even if Websocket is not connected yet.
- Whenever a new websocket client connects, server must dispose of the old websocket and communicate only with the new one

Write this server in C#, you can split it into multiple files.

Write me a Dockerfile (use .NET7) and command how to build the image and then another command to run the container.

### ESP32 client
Write me a script that runs on ESP32 using arduino framework. 
- It connects to UDP server (IP address and port will be hardcoded)
- It receives packets from server. 
- Packets have this 5 byte structure: First byte is header (0xFF), tail byte (last) is 0x00.
- There are currently two types of packets:
  1. Control packet: second byte is type (0x01), third byte is steering, fourth byte is throttle
  2. E2E latency packet: second byte is type (0x03)
- It controls two PWM signals: Steering servo and throttle (motor). The pin numbers are hardcoded.
- It reads PWM on two pins for steering and throttle signal from standard R/C car receiver. Width of those signals is 1000 - 2000 us. The pin numbers are hardcoded.
- Since it receives two signals, they have to be prioritized: The priority lies with R/C receiver signals:
  1. If signals from receiver are not in central position, output those two signals to output PWM pins.
  2. If signals from receiver are in central position, output signals that you receive from UDP server in control packet.
- If it receives E2E latency packet, it responds a similar packet to server: type will be 0x03, and then second byt will be steering as read from receiver, third byte will be throttle from receiver
- Send some UDP packets regularly, e.g. every second so that we keep the connection alive.

### Android streaming app
I want to create a native android application in Kotlin that would find list of available cameras and display them including their characteristics (forward or rear), and angle of view.

### Adroid app deployment
Can you explain me how to deploy (for development purposes) android application written in kotlin to my android phone?