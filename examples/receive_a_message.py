from pywirelessmbus import WMbus
from time import sleep
import asyncio
from pywirelessmbus.devices import Device
from pywirelessmbus.utils import WMbusMessage
import logging

logger = logging.getLogger(__name__)


def main():
    loop = asyncio.get_event_loop()
    wmbus = WMbus("IM871A_USB")

    def handle_device_message(device: Device, message: WMbusMessage):
        logger.info("Receive message per event from device %s:", device.id)

        for value in message.values:
            logger.info(
                "Stored value: %s %s Time: %s",
                value["value"],
                value["unit"],
                value["timestamp"],
            )

    wmbus.on_radio_message = handle_device_message
    wmbus.start()

    loop.run_forever()
    loop.close()


if __name__ == "__main__":
    main()
