from dataclasses import dataclass, field
from wmbus.sticks import IM871A_USB
from wmbus.devices import Device, WeptechOMSv1, WeptechOMSv2
from wmbus.exceptions import UnknownDeviceTypeError, UnknownDeviceVersion
import asyncio
import logging
import struct
from time import sleep
from typing import Optional, Union, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STICK_TYPES = {"IM871A_USB": IM871A_USB}


@dataclass
class WMbus:
    device_type: str
    stick: Optional[Union[IM871A_USB]] = None
    devices: Dict[bytes, Device] = field(default_factory=dict)
    path: str = "/dev/ttyUSB0"

    def __post_init__(self):
        self._started = False
        self._loop = asyncio.get_event_loop()

    def start(self):
        try:
            self.stick = STICK_TYPES[self.device_type](path=self.path)
        except KeyError:
            raise UnknownDeviceTypeError(
                "The choosen device type is unfornatly unknown. Possible variants [IM871A_USB]"
            )

        # register events
        self.stick.on_radio_message = self.process_radio_message

        self.stick.watch()

        self._loop.run_forever()
        self._loop.close()

    def stop(self):
        if self.stick is not None:
            self.stick.stop_watch()

    def process_radio_message(self, message):
        if message.payload.startswith(b"\x44\xb0\x5c"):
            # react on Weptech devices
            serial_number = message.payload[3:7][::-1]
            version = message.payload[7]
            device = None

            if serial_number in self.devices:
                device = self.devices[serial_number]
            else:
                logger.info(
                    "Create new Weptech OMS Device with serial number %s",
                    serial_number.hex(),
                )

                if version == 1:
                    device = WeptechOMSv1(serial_number=serial_number.hex())
                elif version == 2:
                    device = WeptechOMSv2(serial_number=serial_number.hex())
                else:
                    raise UnknownDeviceVersion(
                        "The message belongs to an unsupported version of the Weptech OMS."
                    )

                self.devices[serial_number] = device

            device.process_new_message(message)

        else:
            logger.warning("Got message from unknown device.")


def main():
    wmbus = WMbus("IM871A_USB")
    wmbus.start()

    if wmbus.stick is not None:
        wmbus.stick.ping()

    wmbus.stop()


if __name__ == "__main__":
    main()

