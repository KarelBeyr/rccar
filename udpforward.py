import asyncio
import websockets

class ESP32UDPProtocol:
    def __init__(self, websocket_send):
        self.websocket_send = websocket_send  # Function to send data back to WebSocket
        self.esp32_address = None  # Initially, the ESP32's address is unknown

    def connection_made(self, transport):
        self.transport = transport
        print("UDP connection made")

    def datagram_received(self, data, addr):
        print(f"Received UDP packet from {addr}")
        if not self.esp32_address:
            self.esp32_address = addr  # Store the ESP32's address when the first packet is received
            print(f"ESP32 address set to {self.esp32_address}")
        asyncio.create_task(self.handle_packet(data, addr))
            
    async def handle_packet(self, data, addr):
        # Ensure data is at least 2 bytes long to check packet type
        if len(data) >= 2:
            # Check for E2E latency check packet type (type 3) and forward it to the WebSocket client
            if data[1] == 3:
                await self.websocket_send(data)  # Send the pong back to WebSocket
        else:
            print("Received packet is too short to process.")            

    def error_received(self, exc):
        print('UDP error received:', exc)

    def connection_lost(self, exc):
        print("UDP connection lost:", exc)

    def send_to_esp32(self, data):
        if self.esp32_address:
            self.transport.sendto(data, self.esp32_address)
        else:
            print("ESP32 address not yet known, cannot send data.")

async def handle_websocket(websocket, path, udp_protocol):
    async for message in websocket:
        print("Received WebSocket packet")
        # Correct handling of the incoming WebSocket message
        data = message if isinstance(message, (bytes, bytearray)) else bytearray(message, 'utf-8')
        
        # Simple latency check packet (type 2)
        if data[1] == 2:
            await websocket.send(data)  # Echo back for latency measurement
        
        # Control packet (type 1) or E2E latency check packet (type 3), forward to ESP32
        elif data[1] in [1, 3]:
            udp_protocol.send_to_esp32(data)

async def main():
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: ESP32UDPProtocol(lambda data: asyncio.ensure_future(current_websocket.send(data))),
        local_addr=('0.0.0.0', 12000))

    global current_websocket
    current_websocket = None

    async with websockets.serve(
        lambda ws, path: handle_websocket(ws, path, protocol), '0.0.0.0', 12001):
        await asyncio.Future()  # Run forever

# Start the server
asyncio.run(main())