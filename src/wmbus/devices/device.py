from dataclasses import dataclass
from abc import ABC, abstractmethod


class Device(ABC):
    def __init__(self, device_id: str):
        self.id = device_id

    @abstractmethod
    def process_new_message(self, message):
        pass
