import asyncio
import websockets
import socket

# Create a UDP socket for listening (receiving messages)
udp_listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind it to any IP and a specific port that ESP32 will send data to
udp_listen_sock.bind(("0.0.0.0", 12000))

# This will store the last known address of the ESP32
esp32_address = None

current_websocket = None

async def listen_for_esp32():
    global esp32_address
    global current_websocket
    while True:
        # Wait for data to be available on the socket
        await asyncio.sleep(0.1)  # Non-blocking wait; adjust as needed
        try:
            data, addr = udp_listen_sock.recvfrom(1024, socket.MSG_DONTWAIT)  # Non-blocking call
            print(f"Received message: {data} from {addr}")
            esp32_address = addr  # Update ESP32's address with every packet
            # If it's a pong packet, forward it to the WebSocket client
            if data and len(data) >= 5 and data[0] == 0xFF and data[1] == 0x03 and current_websocket:
                await current_websocket.send(data)
        except BlockingIOError:
            # No data available; continue the loop
            continue

async def handle_websocket(websocket, path):
    global esp32_address
    global current_websocket
    current_websocket = websocket  # Store the current websocket connection
    
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
            
            elif packet_type == 0x03:  # Packet type 3 for ESP32 latency check
                if esp32_address is not None:
                    udp_listen_sock.sendto(message, esp32_address)
                    print(f"Forwarded latency check packet to ESP32 {esp32_address}: {message}")
                else:
                    print("ESP32 address not known yet. Skipping latency check packet forwarding.")
                    
            else:
                packet_contents = ' '.join(f'{byte:02X}' for byte in message)
                print(f"Received unknown packet type: [{packet_contents}]")

        else:
            packet_contents = ' '.join(f'{byte:02X}' for byte in message)
            print(f"Received malformed packet: [{packet_contents}]")

async def main():
    # Start listening for UDP packets in a separate task
    asyncio.create_task(listen_for_esp32())

    # Start the WebSocket server
    async with websockets.serve(handle_websocket, "0.0.0.0", 12001):
        await asyncio.Future()  # Run forever

# Run the main function
asyncio.run(main())