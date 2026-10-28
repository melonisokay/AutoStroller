import asyncio
import struct
from bless import BlessServer, BlessGATTCharacteristic, GATTCharacteristicProperties, GATTAttributePermissions

# Ensure UUID blocks correspond precisely to Swift configurations
SERVICE_UUID = "4A98C721-1234-ABCD-EF01-9876543210AB"
CHAR_UUID    = "4A98C722-1234-ABCD-EF01-9876543210AB"

def write_request_handler(characteristic: BlessGATTCharacteristic, data: bytearray):
    try:
        # Unpack the raw 4-byte stream payload back into an explicit Python Float type
        distance_meters = struct.unpack('<f', data)[0]
        print(f"Received Stream Segment -> Realtime Distance: {distance_meters:.3f} meters")
    except Exception as e:
        print(f"Error parsing inbound telemetry payload packet: {e}")

async def run_server():
    print("Initializing Raspberry Pi 5 Custom BLE GATT Core Server Node...")
    
    # Initialize the bless server with a name visible to your iOS app
    server = BlessServer(name="Pi5-GATT-Server")
    
    # Register endpoints using bless syntax
    await server.add_new_service(SERVICE_UUID)
    await server.add_new_characteristic(
        SERVICE_UUID, 
        CHAR_UUID, 
        properties=GATTCharacteristicProperties.write_without_response | GATTCharacteristicProperties.write, 
        permissions=GATTAttributePermissions.writeable,
        value=bytearray([0x00, 0x00, 0x00, 0x00])
    )
    
    # Bind your callback function to execute whenever the iOS app writes data
    server.write_request = write_request_handler
    
    print("GATT Profile Online. Advertising payload target to iOS device...")
    await server.start()
    
    # Continuous loop keeping the peripheral stack active
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("Shutting down GATT Server...")
    finally:
        await server.stop()

if __name__ == "__main__":
    asyncio.run(run_server())
