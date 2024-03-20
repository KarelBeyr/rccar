# RC car forwarding infrastructure
Forwarding signals joystick/controller connected to computer (phone) to ESP32 connected servos in an RC car.

## Current issues
- [ ] security concerns - anybody can currently hijack my car as everything goes unencrypted over public IP address. How to improve? There could be a password field and forwarding server would validate password hash against some hardcoded value..
- [ ] animate input in FE in a better graphical way, ideally show car with turned wheels, but how to display speed?
- [ ] serve complete HTML web page from websocketforwarding server
- [ ] enable FE control without having any gamepad connected

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

Write this server in C#, you can split it into multiple files.

Write me a Dockerfile (use .NET7) and command how to build the image and then another command to run the container.
