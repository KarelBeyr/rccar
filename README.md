# RC car forwarding infrastructure
Forwarding signals joystick/controller connected to computer (phone) to ESP32 connected servos in an RC car.

## Current issues
- [x] strange delay(25) in each arduino loop - it's there to prevent server flooding. But probably it would be better to initialize server connection at startup (in setup?) and then never send it again. And no delay in loop would be necessary
- [x] startup sequence: I must start the server first, or it might not register esp32 in case it changes it's IP address
- [x] thus probably change logic in python server that whenever it receives a "wakeup" packet from esp32, it rewrites its IP address
- [x] how to measure latency? Would it be possible to create special ping in JS that would send packet through server to esp32, which would pong and JS would measure latency and display it on screen? 
- [x] do I need to create UDP packet "header" and "tail"? If yes, probably I should create {header-FF}-{packetType-1=normal,2=ping}-{steer}-{throttle}-{tail-00}
- [x] do I care about websocket packet payload? If I can create a similar packet structure like in UDP (so that python server is easier (no JSON parsing)) it would be worth it.
- [ ] security concerns - anybody can currently hijack my car as everything goes unencrypted over public IP address. How to improve?
- [ ] animate input in FE in a better graphical way, ideally show car with turned wheels, but how to display speed?
- [x] bug: when websocket restarts, python fails with address already in use

## Nocode GPT input
### Server component
I want to create a forwarding server that accepts packets from Websocket (from client running in browser and written in Javascript) and forwards those packets to UDP (to client running on ESP32 written in Arduino framework).
- Neither of those clients have static IP address. The server must wait for them to connect actively.
- The server should listen on port 12000 for UDP packets and on port 12001 for websocket packets.
- There are currently three types of packets. The server must not modify those packets and it must understand some of them to react to them accordingly:
   1. Control packet. It has 5 byte structure: First byte is header (0xFF), second byte is type (0x01), third byte is steering, fourth byte is throttle and fifth byte is tail (0x00)
   2. Simple latency packet. It has the same 5 byte structure, except for the second byte which is 0x02.
   3. E2E latency packet. It has the same 5 byte structure, except for the third byte which is 0x03.
- The server must immediately send response back to websocket for simple latency packet.
- The server must forward other packets to UDP and in case it receives back some packets from UDP to forward them back into websocket.
- The server must gracefully handle CTR+C to cleanly exit.
- The server needs only to handle a single connection from websocket and a single connection to UDP. However, it must be able to handle both clients to reconnect (e.g. websocket or UDP client can restart and they will initiate new websocket or UDP connection).
- The server must be able to accept websocket communication even if UDP is not connected and perform basic tasks (logging incoming packets, replying to latency packet. Of course it would not forward anything).
- The server must be able to accept UDP communication even if Websocket is not connected yet.
- Write this server in Python in a single file.
- Write me a Dockerfile and command how to build the image and then another command to run the container.
