from pywirelessmbus import WMbus
from time import sleep
import asyncio
from pywirelessmbus.devices import Device
import os
from loguru import logger

logger.enable("pywirelessmbus")

port = os.getenv("SERIAL_PORT") or "/dev/ttyUSB0"


async def main():
    wmbus = WMbus("IM871A_USB", path=port)
    target_device = "b05c74720000021b"

    def handle_new_device(device: Device):
        if device.id == target_device:
            sleep(1)
            device.set_aes_key(
                key=b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F"
            )

    wmbus.on_device_registration = handle_new_device
    await wmbus.start()

    while wmbus.running:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
