from pywirelessmbus.devices import Device
from pywirelessmbus.utils.message import WMbusMessage

from typing import Optional


class MockDevice(Device):
    last_message: Optional[WMbusMessage]

    def __init__(self, *args, **kwargs):
        self.last_message = None
        super().__init__(*args, **kwargs)

    def process_new_message(self, message: WMbusMessage):
        self.last_message = message

        return message
