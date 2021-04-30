from pywirelessmbus import WMbus
import asyncio
from pywirelessmbus.devices import Device
from pywirelessmbus.utils import WMbusMessage
import os
from loguru import logger

logger.enable("pywirelessmbus")

port = os.getenv("SERIAL_PORT") or "/dev/ttyUSB0"


async def main():
    wmbus = WMbus("IM871A_USB", path=port)

    def handle_device_message(device: Device, message: WMbusMessage):
        logger.info("Receive message per event from device {}:", device.id)

        for value in message.values:
            logger.info(
                "Stored value: {} {} Time: {}",
                value.value,
                value.unit,
                value.timestamp,
            )

    wmbus.on_radio_message = handle_device_message
    await wmbus.start()

    while wmbus.running:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
