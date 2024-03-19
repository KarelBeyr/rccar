import asyncio
import websockets
import socket

# Create a UDP socket for listening (receiving messages)
udp_listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind it to any IP and a specific port that ESP32 will send data to
udp_listen_sock.bind(("0.0.0.0", 12000))

# This will store the last known address of the ESP32
esp32_address = None

def listen_for_esp32():
    global esp32_address
    while True:
        # Wait for a message from the ESP32
        data, addr = udp_listen_sock.recvfrom(1024)  # Buffer size is 1024 bytes
        print(f"Received message: {data} from {addr}")
        # Update ESP32's address for future communications
        esp32_address = addr
        break  # Break after the first message to return control to asyncio loop

async def handle_websocket(websocket, path):
    global esp32_address
    while True:
        message = await websocket.recv()
        message = message if isinstance(message, bytearray) else bytearray(message)

        # Handling different packet types without needing ESP32's address for certain operations.
        if len(message) == 5 and message[0] == 0xFF and message[-1] == 0x00:
            packet_type = message[1]
            
            if packet_type == 0x01:  # Control packet
                if esp32_address is not None:  # Check if ESP32's address is known
                    steering = message[2]  # Extract steering byte
                    throttle = message[3]  # Extract throttle byte
                    udp_packet = bytearray([0xFF, packet_type, steering, throttle, 0x00])

                    # Send the constructed packet to the ESP32
                    udp_listen_sock.sendto(udp_packet, esp32_address)
                    print(f"Forwarded message to ESP32 {esp32_address}: {udp_packet}")
                else:
                    print("ESP32 address not known yet. Skipping control packet forwarding.")

            elif packet_type == 0x02:  # Latency test packet
                # Simply echo the packet back to the sender
                await websocket.send(message)
                print(f"Echoed back latency test packet: {message}")
                
            else:
                packet_contents = ' '.join(f'{byte:02X}' for byte in message)
                print(f"Received unknown packet type: [{packet_contents}]")

        else:
            packet_contents = ' '.join(f'{byte:02X}' for byte in message)
            print(f"Received malformed packet: [{packet_contents}]")

async def main():
    # Run the UDP listener in a separate thread to not block asyncio loop
    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, listen_for_esp32)  # Note: Not awaited here

    # Start the WebSocket server
    async with websockets.serve(handle_websocket, "0.0.0.0", 12001):
        await asyncio.Future()  # Run forever

asyncio.run(main())
