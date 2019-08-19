from dataclasses import dataclass
from wmbus.exceptions import InvalidMessageLength
from typing import Optional


@dataclass
class Message:
    endpoint_id: int
    message_id: int
    payload_length: int
    with_timestamp_field: bool
    with_rssi_field: bool
    with_crc_Field: bool
    payload: Optional[bytes] = None
    crc: Optional[bytes] = None
    rssi: Optional[int] = None
    timestamp: Optional[bytes] = None

    def check_message_length(self):
        if payload is None:
            raise AttributeError("Need a payload to check message length.")

        if (
            len(self.payload)
            != 4
            + self.payloadLength
            + (self.with_timestamp_field is not None) * 4
            + (self.with_rssi_field is not None)
            + (self.with_crc_Field is not None) * 2
        ):
            raise InvalidMessageLength(
                f"The length of the message '{message} differ from the given."
            )

        return true
