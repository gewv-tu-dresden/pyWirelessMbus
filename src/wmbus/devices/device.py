from dataclasses import dataclass
from abc import ABC, abstractmethod


class Device(ABC):
    def __init__(self, serial_number: str):
        self.serial_number = serial_number

    @abstractmethod
    def process_new_message(self, message):
        pass
