from abc import ABC, abstractmethod
from typing import Callable, Optional, Any
from pywirelessmbus.utils import WMbusMessage
from pywirelessmbus.utils.utils import NOOP


class Device(ABC):
    on_set_aes_key: Callable[[int, str, bytes], None]

    def __init__(
        self,
        device_id: str,
        index: int,
        label: str = "",
        on_set_aes_key=NOOP,
        ctx: Optional[Any] = None,
    ):
        self.id = device_id
        self.index = index
        self.on_set_aes_key = on_set_aes_key
        self.label = label
        self.ctx = ctx

    @abstractmethod
    def process_new_message(self, message: WMbusMessage) -> WMbusMessage:
        pass

    def set_aes_key(self, key: bytes):
        self.on_set_aes_key(self.index, self.id, key)
