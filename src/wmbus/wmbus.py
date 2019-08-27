from dataclasses import dataclass, field
from wmbus.sticks import IM871A_USB
from wmbus.devices import Device, WeptechOMSv1, WeptechOMSv2, MockDevice, EnergyCam
from wmbus.exceptions import UnknownDeviceTypeError, UnknownDeviceVersion
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
    on_radio_message: Callable[[Device], None] = NOOP
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

    def process_radio_message(self, message):
        # 44 -> SND_NR (Send, No Response)
        if not message.payload.startswith(b"\x44"):
            logger.warning("Unknown radio message.")
            return

        manufacturer_id = message.payload[1:3]
        serial_number = message.payload[3:7]
        version = message.payload[7:8]
        device_type = message.payload[8:9]
        device = None
        device_id = manufacturer_id + serial_number + version + device_type

        if device_id in self.devices:
            device = self.devices[device_id]
        else:
            # try to find manufacturar for message
            if manufacturer_id == WEPTECH:
                if version == b"\x01":
                    # Temp Sensor
                    device = WeptechOMSv1(
                        device_id=device_id.hex(),
                        index=len(self.devices),
                        stick=self.stick,
                    )
                elif version == b"\x02":
                    # Temp/Hum Sensor
                    device = WeptechOMSv2(
                        device_id=device_id.hex(),
                        index=len(self.devices),
                        stick=self.stick,
                    )
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
                    device = EnergyCam(
                        device_id=device_id.hex(),
                        meter_type=meter_type,
                        index=len(self.devices),
                        stick=self.stick,
                    )
                else:
                    logger.error(
                        "The message belongs to an unsupported fastforward device. Version: %s",
                        version,
                    )
                    return

            elif manufacturer_id == MOCK:
                device = MockDevice(
                    device_id=device_id.hex(), index=len(self.devices), stick=self.stick
                )
            else:
                logger.warning(
                    "Got message from unknown manufactur: %s", manufacturer_id
                )
                return

            logger.info("Create new Device with id %s", device_id.hex())
            self.devices[device_id] = device
            self.on_device_registration(device)

        processed_message = device.process_new_message(message)
        self.on_radio_message(device, processed_message)

