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

    await wmbus.start()
    wmbus.stick.link_mode = "T2"

    while wmbus.running:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
