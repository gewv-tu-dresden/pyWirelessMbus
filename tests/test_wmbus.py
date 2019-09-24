from wmbus import WMbus
import pty
import pytest
import os
from time import sleep
from wmbus.sticks import MockStick
from wmbus.utils import IMSTMessage, WMbusMessage
from wmbus.devices import MockDevice, Device
from dataclasses import dataclass


@dataclass
class Context:
    device: Device = None
    message: WMbusMessage = None
    message_device: Device = None

    def handle_device_registration(self, device: Device):
        self.device = device

    def handle_message(self, device: Device, message: WMbusMessage):
        self.message = message
        self.message_device = device


@pytest.fixture
def virtual_serial():
    master, slave = pty.openpty()
    return master, slave


def test_init(virtual_serial):
    master, slave = virtual_serial
    wMbus = WMbus("IM871A_USB", path=os.ttyname(slave))

    assert type(wMbus) == WMbus


def test_runtime(virtual_serial):
    master, slave = virtual_serial
    wMbus = WMbus("IM871A_USB", path=os.ttyname(slave))

    wMbus.start()
    sleep(0.5)
    assert wMbus.running
    wMbus.stop()
    assert not wMbus.running


def test_process_radio_message(virtual_serial):
    master, slave = virtual_serial
    context = Context()

    stick = MockStick()
    wMbus = WMbus(
        "IM871A_USB",
        path=os.ttyname(slave),
        on_device_registration=context.handle_device_registration,
        on_radio_message=context.handle_message,
        stick=stick,
    )

    message = IMSTMessage(
        endpoint_id=0,
        message_id=0,
        payload_length=4,
        with_timestamp_field=False,
        with_crc_field=False,
        with_rssi_field=False,
        payload=b"\x12\x44\xff\xff\x12\xaa\xaa\xbb\x12\x13\x14\x15\x12\x13\x14\x15",
    )

    wMbus.process_radio_message(message)

    assert context.device is not None
    assert type(context.device) == MockDevice
    assert type(context.message) == WMbusMessage
    assert type(context.message_device) == MockDevice

    assert context.device.id == "ffff12aaaabb1213"
    assert context.message_device.id == "ffff12aaaabb1213"

    assert context.message.access_number == 21
    assert context.message.command == b"\x44"
    assert context.message.configuration_word == b"\x13"
    assert context.message.control_field == b"\x14"
    assert context.message.device_type == b"\x13"
    assert context.message.length == 18
    assert context.message.manufacturer_id == b"\xff\xff"
    assert (
        context.message.raw
        == b"\x12\x44\xff\xff\x12\xaa\xaa\xbb\x12\x13\x14\x15\x12\x13\x14\x15"
    )
    assert context.message.serial_number == b"\xff\x12\xaa\xaa\xbb"
    assert context.message.status == 18
    assert context.message.version == b"\x12"
