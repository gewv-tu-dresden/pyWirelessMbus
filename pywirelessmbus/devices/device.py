from abc import ABC, abstractmethod
from typing import Callable
from pywirelessmbus.utils import WMbusMessage
import logging
from pywirelessmbus.utils.utils import NOOP

logger = logging.getLogger(__name__)


class Device(ABC):
    on_set_aes_key: Callable[[int, str, bytes], None]

    def __init__(self, device_id: str, index: int, on_set_aes_key=NOOP):
        self.id = device_id
        self.index = index
        self.on_set_aes_key = on_set_aes_key

    @abstractmethod
    def process_new_message(self, message: WMbusMessage) -> WMbusMessage:
        pass

    def set_aes_key(self, key: bytes):
        self.on_set_aes_key(self.index, self.id, key)
