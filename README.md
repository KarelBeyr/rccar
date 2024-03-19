Forwarding signals joystick/controller connected to computer (phone) to ESP32 connected servos in an RC car.

current issues:
* strange delay(25) in each arduino loop - it's there to prevent server flooding. But probably it would be better to initialize server connection at startup (in setup?) and then never send it again. And no delay in loop would be necessary
* startup sequence: I must start the server first, or it might not register esp32 in case it changes it's IP address
 * thus probably change logic in python server that whenever it receives a "wakeup" packet from esp32, it rewrites its IP address
* how to measure latency? Would it be possible to create special ping in JS that would send packet through server to esp32, which would pong and JS would measure latency and display it on screen? 
* do I need to create UDP packet "header" and "tail"? If yes, probably I should create {header-FF}-{packetType-1=normal,2=ping}-{steer}-{throttle}-{tail-00}
* do I care about websocket packet payload? If I can create a similar packet structure like in UDP (so that python server is easier (no JSON parsing)) it would be worth it.
- security concerns - anybody can currently hijack my car as everything goes unencrypted over public IP address. How to improve?
- animate input in FE in a better graphical way, ideally show car with turned wheels, but how to display speed?
- bug: when websocket restarts, python fails with address already in use
