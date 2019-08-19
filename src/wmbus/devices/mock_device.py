from wmbus.devices import Device
from wmbus.utils.message import Message

from typing import Optional


class MockDevice(Device):
    last_message: Optional[Message]

    def __init__(self, *args, **kwargs):
        self.last_message = None
        super().__init__(*args, **kwargs)

    def process_new_message(self, message: Message):
        self.last_message = message
