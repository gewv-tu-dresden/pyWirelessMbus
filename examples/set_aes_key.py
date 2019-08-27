from wmbus import WMbus
from time import sleep
import asyncio
from wmbus.devices import Device
import logging

logger = logging.getLogger(__name__)


def main():
    loop = asyncio.get_event_loop()
    wmbus = WMbus("IM871A_USB")
    target_device = "b05c74720000021b"

    def handle_new_device(device: Device):
        if device.id == target_device:
            sleep(1)
            device.set_aes_key(
                key=b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F"
            )

    wmbus.on_device_registration = handle_new_device
    wmbus.start()

    loop.run_forever()
    loop.close()


if __name__ == "__main__":
    main()

