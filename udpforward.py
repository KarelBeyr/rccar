import asyncio
import websockets
import json
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
        if esp32_address is None:
            print("ESP32 address not known yet.")
            continue  # Skip if we don't have the ESP32's address

        # data = json.loads(message)
        # steering = data['steering']
        # throttle = data['throttle']
        # udp_packet = bytearray([0xFF, steering, throttle, 0x00])
        if len(message) == 5 and message[0] == 0xFF and message[-1] == 0x00 and message[1] == 0x01:
            steering = message[2]  # Extract steering byte
            throttle = message[3]  # Extract throttle byte
            # Now, 'steering' and 'throttle' are the byte values directly from the packet
            # You can use these values as is or convert them if needed
            # Construct UDP packet (though it might be redundant depending on your use case)
            udp_packet = bytearray([0xFF, steering, throttle, 0x00])

            # Send the constructed packet to the ESP32
            udp_listen_sock.sendto(udp_packet, esp32_address)
            print(f"Forwarded message to ESP32 {esp32_address}: {udp_packet}")

        else:
            packet_contents = ' '.join(f'{byte:02X}' for byte in message)
            print(f"Received malformed packet: [{packet_contents}]")


async def main():
    # Run the UDP listener in a separate thread to not block asyncio loop
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, listen_for_esp32)

    # Start the WebSocket server
    async with websockets.serve(handle_websocket, "0.0.0.0", 12001):
        await asyncio.Future()  # Run forever

asyncio.run(main())


# import asyncio
# import websockets
# import json
# import socket

# # Create a UDP socket for listening (receiving messages)
# udp_listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# # Bind it to any IP and a specific port that ESP32 will send data to
# udp_listen_sock.bind(("0.0.0.0", 12000))

# # This will store the last known address of the ESP32
# esp32_address = None

# async def listen_for_esp32():
    # global esp32_address
    # while True:
        # # Wait for a message from the ESP32
        # data, addr = udp_listen_sock.recvfrom(1024)  # Buffer size is 1024 bytes
        # print(f"Received message: {data} from {addr}")
        # # Update ESP32's address for future communications
        # esp32_address = addr

# async def handle_websocket(websocket, path):
    # global esp32_address
    # async for message in websocket:
        # if esp32_address is None:
            # print("ESP32 address not known yet.")
            # continue  # Skip if we don't have the ESP32's address

        # data = json.loads(message)
        # steering = data['steering']
        # throttle = data['throttle']
        # udp_packet = bytearray([0xFF, steering, throttle, 0x00])

        # # Send the constructed packet to the ESP32
        # udp_listen_sock.sendto(udp_packet, esp32_address)
        # print(f"Forwarded message to ESP32 {esp32_address}: {udp_packet}")

# # Run the UDP listener in a separate asyncio task
# async def main():
    # udp_task = asyncio.create_task(listen_for_esp32())
    # ws_task = await websockets.serve(handle_websocket, "0.0.0.0", 12001)
    # await asyncio.gather(udp_task, ws_task)

# asyncio.run(main())
