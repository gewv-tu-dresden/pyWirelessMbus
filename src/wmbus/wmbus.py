from dataclasses import dataclass, field
from wmbus.sticks import IM871A_USB
from wmbus.devices import Device, WeptechOMSv1, WeptechOMSv2, MockDevice, EnergyCam
from wmbus.exceptions import UnknownDeviceTypeError, UnknownDeviceVersion
import asyncio
import logging
import struct
from time import sleep
from typing import Optional, Union, Dict
from os import environ

logging.basicConfig(level=getattr(logging, environ.get("LOG_LEVEL") or "INFO"))
logger = logging.getLogger(__name__)

STICK_TYPES = {"IM871A_USB": IM871A_USB}

# Manufacturer
WEPTECH = b"\x5c\xb0"
FASTFORWARD = b"\x18\xc4"
IMST = b"\x25\xb3"
MOCK = b"\xff\xff"


@dataclass
class WMbus:
    device_type: str
    stick: Optional[Union[IM871A_USB]] = None
    devices: Dict[bytes, Device] = field(default_factory=dict)
    path: str = "/dev/ttyUSB0"

    def __post_init__(self):
        self.running = False
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
        self.running = True
        self.stick.watch()

    def stop(self):
        if self.stick is not None:
            self.stick.stop_watch()
            self.running = False

    def process_radio_message(self, message):
        # 44 -> SND_NR (Send, No Response)
        if not message.payload.startswith(b"\x44"):
            logger.warning("Unknown radio message.")
            return

        manufacturer_id = message.payload[1:3][::-1]
        serial_number = message.payload[3:7][::-1]
        version = message.payload[7:8]
        device = None
        device_id = manufacturer_id + serial_number + version

        if device_id in self.devices:
            device = self.devices[device_id]
        else:
            # try to find manufacturar for message
            if manufacturer_id == WEPTECH:
                if version == b"\x01":
                    # Temp Sensor
                    device = WeptechOMSv1(device_id=device_id.hex())
                elif version == b"\x02":
                    # Temp/Hum Sensor
                    device = WeptechOMSv2(device_id=device_id.hex())
                else:
                    logger.error(
                        "The message belongs to an unsupported weptech device. Version: %s",
                        version,
                    )
                    return

            elif manufacturer_id == FASTFORWARD:
                if version == b"\x01":
                    # Energy Cam
                    meter_type = message.payload[8]
                    device = EnergyCam(device_id=device_id.hex(), meter_type=meter_type)
                else:
                    logger.error(
                        "The message belongs to an unsupported fastforward device. Version: %s",
                        version,
                    )
                    return

            elif manufacturer_id == MOCK:
                device = MockDevice(device_id=device_id)
            else:
                logger.warning(
                    "Got message from unknown manufactur: %s", manufacturer_id
                )
                return

            logger.info("Create new Device with id %s", device_id.hex())
            self.devices[device_id] = device

        device.process_new_message(message)

