from wmbus import WMbus
from time import sleep
import asyncio
from wmbus.devices import Device
import logging

logger = logging.getLogger(__name__)


def main():
    loop = asyncio.get_event_loop()
    wmbus = WMbus("IM871A_USB")

    wmbus.start()
    wmbus.stick.link_mode = "T2"

    loop.run_forever()
    loop.close()


if __name__ == "__main__":
    main()
