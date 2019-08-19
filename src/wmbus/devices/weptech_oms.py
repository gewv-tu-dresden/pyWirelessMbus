from wmbus.devices import Device
from wmbus.utils.message import Message
from typing import Optional
from time import time
from datetime import datetime
from wmbus.exceptions import InvalidMessageLength
import logging

logger = logging.getLogger(__name__)


class WeptechOMS(Device):
    updated_at: Optional[float]
    status: int
    temperatur: float
    counter: int

    def __init__(self, *args, **kwargs):
        self.updated_at = None
        self.status = 0
        self.temperatur = -300
        self.counter = -1

        super().__init__(*args, **kwargs)

    def process_new_message(self, message: Message):
        self.counter = message.payload[10]
        self.status = message.payload[11]
        self.updated_at = time()

        logger.info(
            "Receive new measurement from Weptech OMS Device %s", self.serial_number
        )
        logger.debug("Counter: %s", self.counter)
        logger.debug("Status: %s", bin(self.status))
        logger.info(
            "Timestamp: %s",
            datetime.utcfromtimestamp(self.updated_at).strftime("%Y-%m-%d %H:%M:%S"),
        )

        # decode humidity
        self.temperatur = self.decode_value_block(message.payload[18:20])
        logger.info("Temperature: %s °C", self.temperatur)

    @staticmethod
    def decode_value_block(block: bytes) -> float:
        if block[1] < 0xA0:
            number_1 = int(block[0:1].hex()) / 10
            number_2 = int(block[1:2].hex()) * 10
        else:
            number_1 = -int(block[0:1].hex()) / 10
            number_2 = -int(block[1] ^ 240) * 10
        return number_1 + number_2


class WeptechOMSv1(WeptechOMS):
    version: int
    sensor_type: str

    def __init__(self, *args, **kwargs):
        self.version = 1
        self.sensor_type = "Temp Sensor"

        super().__init__(*args, **kwargs)

    def process_new_message(self, message: Message):
        if message.payload_length != 30:
            raise InvalidMessageLength(
                "Messages from the WeptechOMS should 30 bytes long."
            )

        super().process_new_message(message)


class WeptechOMSv2(WeptechOMS):
    version: int
    sensor_type: str
    humidity: Optional[float]

    def __init__(self, *args, **kwargs):
        self.version = 2
        self.sensor_type = "Temp/Hum Sensor"
        self.humidity = None

        super().__init__(*args, **kwargs)

    def process_new_message(self, message: Message):
        if message.payload_length != 46:
            raise InvalidMessageLength(
                "Messages from the WeptechOMS should 44 bytes long."
            )

        super().process_new_message(message)

        # decode humidity
        self.humidity = self.decode_value_block(message.payload[23:25])
        logger.info("Humidity: %s %%", self.humidity)
