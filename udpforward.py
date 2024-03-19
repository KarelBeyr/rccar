import asyncio
import websockets

class ESP32UDPProtocol:
    def __init__(self, send_to_websocket_callback):
        self.send_to_websocket_callback = send_to_websocket_callback
        self.esp32_address = None

    def connection_made(self, transport):
        self.transport = transport
        print("UDP connection made")

    def datagram_received(self, data, addr):
        print(f"Received UDP packet from {addr}")
        if not self.esp32_address:
            self.esp32_address = addr  # Store the ESP32's address when the first packet is received
            print(f"ESP32 address set to {self.esp32_address}")
        asyncio.create_task(self.handle_packet(data))

    async def handle_packet(self, data):
        if len(data) < 2:
            print("Received packet is too short to process.")
            return
        if data[1] == 3:  # Check for E2E latency packet type
            await self.send_to_websocket_callback(data)

    def error_received(self, exc):
        print('UDP error received:', exc)

    def connection_lost(self, exc):
        print("UDP connection lost:", exc)

    def send_to_esp32(self, data):
        if self.esp32_address:
            self.transport.sendto(data, self.esp32_address)
        else:
            print("ESP32 address not yet known, cannot send data.")

current_websocket = None

async def handle_websocket(websocket, path):
    global current_websocket  # Declare it global here if we intend to modify it
    current_websocket = websocket

    async def send_to_websocket(data):
        # Directly use current_websocket without declaring it global or nonlocal since it's just being accessed here
        if current_websocket:
            await current_websocket.send(data)
        else:
            print("WebSocket connection not established.")

    loop = asyncio.get_running_loop()
    _, protocol = await loop.create_datagram_endpoint(
        lambda: ESP32UDPProtocol(send_to_websocket),
        local_addr=('0.0.0.0', 12000))

    try:
        async for message in websocket:
            if len(message) >= 5 and message[0] == 0xFF:
            
                # Simple latency check packet (type 2)
                if message[1] == 2:
                    await send_to_websocket(message)  # Echo back for latency measurement
            
                if message[1] in [0x01, 0x03]:  # Control or E2E latency packets
                    protocol.send_to_esp32(message)
    finally:
        current_websocket = None  # It's safe to modify it here after declaring global at the beginning of the function

async def main():
    server = await websockets.serve(handle_websocket, "0.0.0.0", 12001)

    try:
        await asyncio.Future()  # Run indefinitely until KeyboardInterrupt
    except asyncio.CancelledError:
        # Handle task cancellations here if any
        pass
    except KeyboardInterrupt:
        # Handle any cleanup here
        print("Program terminated, cleaning up...")
    finally:
        server.close()
        await server.wait_closed()
        # If you have other cleanup tasks, perform them here
        print("Cleanup complete, program exiting.")

# Run the server with graceful shutdown handling
asyncio.run(main())