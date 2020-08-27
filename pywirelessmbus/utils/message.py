from dataclasses import dataclass
from pywirelessmbus.exceptions import InvalidMessageLength
from typing import Optional, List, Dict, Any
import time


@dataclass
class IMSTMessage:
    """
    Messagen, that was produced from the IM871 stick.
    """

    endpoint_id: int
    message_id: bytes
    payload_length: int
    with_timestamp_field: bool
    with_rssi_field: bool
    with_crc_field: bool
    payload: Optional[bytes] = None
    crc: Optional[bytes] = None
    rssi: Optional[int] = None
    timestamp: Optional[bytes] = None

    def check_message_length(self):
        if self.payload is None:
            raise AttributeError("Need a payload to check message length.")

        if (
            len(self.payload)
            != 4
            + self.payload_length
            + (self.with_timestamp_field is not None) * 4
            + (self.with_rssi_field is not None)
            + (self.with_crc_field is not None) * 2
        ):
            raise InvalidMessageLength(
                f"The length of the message {self.message_id} differ from the given."
            )

        return True


class WMbusMessage:
    length: int
    manufacturer_id: bytes
    serial_number: bytes
    version: bytes
    device_type: bytes
    control_field: bytes
    access_number: int
    status: int
    raw: bytes
    values: List[Dict[str, Any]]

    def __init__(self, raw_message):
        self.raw = raw_message.payload

        # Link Layer
        ## L-Field
        self.length = raw_message.payload[0]
        ## C-Field
        self.command = raw_message.payload[1:2]
        ## M-Field
        self.manufacturer_id = raw_message.payload[2:4]
        ## A-Field
        self.serial_number = raw_message.payload[3:8]
        self.version = raw_message.payload[8:9]
        self.device_type = raw_message.payload[9:10]

        ## CRC0
        ## TODO: Implement byte 10 and 11 if exists

        ## CI Field
        self.control_field = raw_message.payload[10:11]
        self.access_number = raw_message.payload[11]
        self.status = raw_message.payload[12]
        self.configuration_word = raw_message.payload[13:14]
        self.values = []

        ## CRC1
        ## TODO: Implement byte 28 and 29 if exists

    def add_value(self, value: float, timestamp: float = None, unit: str = "unset"):
        if value is None:
            raise ValueError("Cant add empty value to processed message.")

        if timestamp is None:
            timestamp = time.time()

        self.values.append({"value": value, "unit": unit, "timestamp": timestamp})
