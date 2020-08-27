from pywirelessmbus.devices import Device
from pywirelessmbus.utils.message import WMbusMessage
from typing import Optional
from time import time
from datetime import datetime
from pywirelessmbus.exceptions import InvalidMessageLength
import logging

logger = logging.getLogger(__name__)


class WeptechOMS(Device):
    updated_at: Optional[float]
    status: int

    def __init__(self, *args, **kwargs):
        self.updated_at = None
        self.status = 0

        super().__init__(*args, **kwargs)

    def process_new_message(self, message: WMbusMessage) -> WMbusMessage:
        try:
            value = self.decode_value_block(message.raw[19:21])
            message.add_value(value, unit="°C")
            logger.info("Temperature: %s °C", value)
        except ValueError:
            logger.error(
                "Failed to decode the temperature value of the webtech oms device %s. Maybe AES encryption is activated.",
                self.id,
            )

        self.updated_at = time()
        logger.info("Receive new measurement from Weptech OMS Device %s", self.id)
        logger.debug("Counter: %s", message.access_number)
        logger.debug("Status: %s", bin(message.status))
        logger.info(
            "Timestamp: %s",
            datetime.utcfromtimestamp(self.updated_at).strftime("%Y-%m-%d %H:%M:%S"),
        )

        return message

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

    def process_new_message(self, message: WMbusMessage) -> WMbusMessage:
        if message.length != 30:
            raise InvalidMessageLength(
                "Messages from the WeptechOMS should 30 bytes long."
            )

        return super().process_new_message(message)


class WeptechOMSv2(WeptechOMS):
    version: int
    sensor_type: str

    def __init__(self, *args, **kwargs):
        self.version = 2
        self.sensor_type = "Temp/Hum Sensor"
        super().__init__(*args, **kwargs)

    def process_new_message(self, message: WMbusMessage) -> WMbusMessage:
        if message.length != 46:
            raise InvalidMessageLength(
                "Messages from the WeptechOMS should 46 bytes long."
            )

        wmbus_message = super().process_new_message(message)
        if wmbus_message is None:
            raise TypeError("Receive None from super method to process new messages.")

        # decode humidity
        try:
            value = self.decode_value_block(message.raw[24:26])
            wmbus_message.add_value(value, unit="%")
            logger.info("Humidity: %s %%", value)
        except ValueError:
            logger.error(
                "Failed to decode the humidity value of the webtech oms device %s. Maybe AES encryption is activated.",
                self.id,
            )

        return wmbus_message
