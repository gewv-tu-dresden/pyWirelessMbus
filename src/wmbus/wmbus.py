from dataclasses import dataclass, field
from wmbus.sticks import IM871A_USB
from wmbus.devices import Device, WeptechOMSv1, WeptechOMSv2, MockDevice, EnergyCam
from wmbus.exceptions import UnknownDeviceTypeError, UnknownDeviceVersion
from wmbus.utils import WMbusMessage
from wmbus.utils import IMSTMessage
import asyncio
import logging
import struct
from time import sleep
from typing import Optional, Union, Dict, Callable, Any
from os import environ

logging.basicConfig(level=getattr(logging, environ.get("LOG_LEVEL") or "INFO"))
logger = logging.getLogger(__name__)

STICK_TYPES = {"IM871A_USB": IM871A_USB}
NOOP = lambda *args: None

# Manufacturer
WEPTECH = b"\x5c\xb0"[::-1]
FASTFORWARD = b"\x18\xc4"[::-1]
IMST = b"\x25\xb3"[::-1]
MOCK = b"\xff\xff"[::-1]


@dataclass
class WMbus:
    device_type: str
    stick: Optional[Union[IM871A_USB]] = None
    devices: Dict[bytes, Device] = field(default_factory=dict)
    path: str = "/dev/ttyUSB0"
    on_device_registration: Callable[[Device], None] = NOOP
    on_radio_message: Callable[[Device, WMbusMessage], None] = NOOP
    on_start: Callable[[], None] = NOOP
    on_stop: Callable[[], None] = NOOP

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
        self.on_start()

    def stop(self):
        if self.stick is not None:
            self.stick.stop_watch()
            self.running = False
            self.on_stop()

    def process_radio_message(self, message: IMSTMessage):
        if message.payload is None:
            return

        # 44 -> SND_NR (Send, No Response)
        if not message.payload[1:2] == b"\x44":
            logger.warning("Unknown radio message.")
            return

        device = None
        device_id = message.payload[2:10]
        wmbus_message = WMbusMessage(message)

        logger.debug("Decoded to following wireless mbus message:")
        logger.debug("Manufactur ID: %s", wmbus_message.manufacturer_id[::-1].hex())
        logger.debug("Serial Number: %s", wmbus_message.serial_number[::-1].hex())
        logger.debug("Version: %s", wmbus_message.version.hex())
        logger.debug("Device Type: %s", wmbus_message.device_type.hex())

        if device_id in self.devices:
            device = self.devices[device_id]
        else:
            # try to find manufacturar for message
            if wmbus_message.manufacturer_id == WEPTECH:
                if wmbus_message.version == b"\x01":
                    # Temp Sensor
                    device = WeptechOMSv1(
                        device_id=device_id.hex(),
                        index=len(self.devices),
                        stick=self.stick,
                    )
                elif wmbus_message.version == b"\x02":
                    # Temp/Hum Sensor
                    device = WeptechOMSv2(
                        device_id=device_id.hex(),
                        index=len(self.devices),
                        stick=self.stick,
                    )
                else:
                    logger.error(
                        "The message belongs to an unsupported weptech device. Version: %s",
                        wmbus_message.version,
                    )
                    return

            elif wmbus_message.manufacturer_id == FASTFORWARD:
                if wmbus_message.version == b"\x01":
                    # Energy Cam
                    meter_type = message.payload[9]
                    device = EnergyCam(
                        device_id=device_id.hex(),
                        meter_type=meter_type,
                        index=len(self.devices),
                        stick=self.stick,
                    )
                else:
                    logger.error(
                        "The message belongs to an unsupported fastforward device. Version: %s",
                        wmbus_message.version,
                    )
                    return

            elif wmbus_message.manufacturer_id == MOCK:
                device = MockDevice(
                    device_id=device_id.hex(), index=len(self.devices), stick=self.stick
                )
            else:
                logger.warning(
                    "Got message from unknown manufactur: %s",
                    wmbus_message.manufacturer_id,
                )
                return

            logger.info("Create new Device with id %s", device_id.hex())
            self.devices[device_id] = device
            self.on_device_registration(device)

        processed_message = device.process_new_message(wmbus_message)
        self.on_radio_message(device, processed_message)

