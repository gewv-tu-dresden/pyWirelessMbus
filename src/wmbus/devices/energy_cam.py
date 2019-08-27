from wmbus.devices import Device
from wmbus.utils.message import IMSTMessage
from wmbus.utils.message import WMbusMessage
from typing import Optional
from time import time
from datetime import datetime
from wmbus.exceptions import InvalidMessageLength
import logging

logger = logging.getLogger(__name__)

METER_TYPE = {1: "Oil", 2: "Energy (electricity)", 3: "Gas", 7: "Water", 15: "Unknown"}


class EnergyCam(Device):
    updated_at: Optional[float]
    meter_type: int

    def __init__(self, meter_type, *args, **kwargs):
        self.updated_at = None
        self.meter_type = meter_type

        super().__init__(*args, **kwargs)

    def process_new_message(self, message: WMbusMessage) -> WMbusMessage:
        logger.info(
            "Got new message from %s meter with ID: %s",
            METER_TYPE[self.meter_type],
            self.id,
        )
        logger.info("Raw Message: %s", message.raw.hex())

        return WMbusMessage(message)
