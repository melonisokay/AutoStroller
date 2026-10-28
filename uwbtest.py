#UWB Test 

import asyncio
import struct
from bleak import BleakGATTCharacteristic
from bleak.backends.peripheral.builtin import PeripheralServer

# Ensure UUID blocks correspond precisely to Swift Configuration
SERVICE_UUID = "4A98C721-1234-ABCD-EF01-9876543210AB"
CHAR_UUID = "4A98C722-1234-ABCD-EF01-9876543210AB"

def write_request_handler(characteristic: BleakGATTCharacteristic, data: bytearray):
    try:
        # Unpack the raw 4-byte stream payload back into an explicit Python Float type
        distance_meters = struct.unpack('<f',data)[0]
        print(f"Received Stream Segment -> Realtime Distance: {distance_meters:.3f} meters")
    except Exception as e:
        print(f"Error parsing inbound telemetry payload packet: {e}")

async def run_server():
    print("Initializing Raspberry Pi 5 Custom BLE GATT Core Server Node...")
    server = PeripheralServer()

    # Register endpoints 
    await server.add_service(SERVICE_UUID)
    await server.add_characteristic(
        SERVICE_UUID, 
        CHAR_UUID, 
        properties = ["write-without-response"],
        value = bytearray([0x00, 0x00, 0x00, 0x00]),
        write_callback = write_request_handler
        )

    print("GATT Profile Online. Advertising payload target to iOS device...")
    await server.start()

    # Continous looop keeping the peripheral stack active
    while True: 
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(run_server())