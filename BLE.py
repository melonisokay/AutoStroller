
import asyncio
import json
import time

from bless import (
    BlessServer,
    GATTCharacteristicProperties,
    GATTAttributePermissions,
)

SERVICE_UUID = "7A1E0001-1234-5678-1234-56789ABCDEF0"
CHAR_UUID = "7A1E0002-1234-5678-1234-56789ABCDEF0"


def on_write(characteristic, value, **kwargs):
    try:
        message = json.loads(bytes(value).decode("utf-8"))
        distance = float(message["distance_m"])
        timestamp = float(message.get("timestamp", time.time()))

        if not (0 <= distance < float("inf")):
            raise ValueError("Invalid distance")

        print(
            f"Distance: {distance:.3f} m | "
            f"Timestamp: {timestamp:.3f}"
        )
    except (ValueError, TypeError, KeyError) as exc:
        print(f"Invalid measurement: {exc}")


async def main():
    server = BlessServer(name="Pi5-Distance")
    server.write_request_func = on_write

    await server.add_gatt_service(SERVICE_UUID)

    await server.add_new_characteristic(
        SERVICE_UUID,
        CHAR_UUID,
        GATTCharacteristicProperties.write
        | GATTCharacteristicProperties.write_without_response,
        None,
        GATTAttributePermissions.writeable,
    )

    await server.start()
    print("Advertising Pi5-Distance; waiting for iPhone...")

    try:
        while True:
            await asyncio.sleep(1)
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
