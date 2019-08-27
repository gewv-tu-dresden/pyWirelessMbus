from wmbus import WMbus
import pty
import pytest
import os
from time import sleep
from wmbus.utils import Message
from wmbus.devices import MockDevice


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
    wMbus = WMbus("IM871A_USB", path=os.ttyname(slave))

    message = Message(
        endpoint_id=0,
        message_id=0,
        payload_length=4,
        with_timestamp_field=False,
        with_crc_field=False,
        with_rssi_field=False,
        payload=b"\x44\xff\xff\x12\xaa\xaa\xbb",
    )

    wMbus.process_radio_message(message)
    device = wMbus.devices[b"\xff\xff\xbb\xaa\xaa\x12"]
    assert device is not None
    assert type(device) == MockDevice
    assert device.last_message == message
