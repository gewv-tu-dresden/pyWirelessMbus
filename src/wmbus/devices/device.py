from dataclasses import dataclass
from abc import ABC, abstractmethod
from wmbus.sticks import IM871A_USB
from typing import Optional, Any, List, Dict
from wmbus.utils import WMbusMessage
import logging

logger = logging.getLogger(__name__)


class Device(ABC):
    _ref_stick: Optional[IM871A_USB]

    def __init__(self, device_id: str, index: int, stick: IM871A_USB = None):
        self.id = device_id
        self.index = index
        self._ref_stick = stick

    @abstractmethod
    def process_new_message(self, message: WMbusMessage) -> WMbusMessage:
        pass

    def set_aes_key(self, key: bytes):
        if self._ref_stick is None:
            logger.warn(
                "Set a aes for the device %s is not possible. The device has no referenz stick."
            )
            return

        self._ref_stick.set_aes_decryption_key(
            table_index=self.index, device_id=self.id, key=key
        )
