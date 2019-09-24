import pytest
from wmbus.devices import WeptechOMSv2, WeptechOMSv1
from wmbus.utils import WMbusMessage, IMSTMessage


def test_init_v1():
    device = WeptechOMSv1(device_id="device_id", index=0)
    assert type(device) == WeptechOMSv1


def test_init_v2():
    device = WeptechOMSv2(device_id="device_id", index=0)
    assert type(device) == WeptechOMSv2


def test_process_message_v1():
    device = WeptechOMSv1(device_id="device_id", index=0)
    raw_message = IMSTMessage(
        endpoint_id=2,
        message_id=3,
        payload_length=30,
        with_timestamp_field=False,
        with_crc_field=False,
        with_rssi_field=False,
        payload=b"\x1e\x44\xb0\x5c\x74\x72\x00\x00\x02\x1b\x7a\xbf\x00\x00\x00\x2f\x2f\x0a\x66\x39\x02\x0a\xfb\x1a\x00\x05\x02\xfd\x97\x1d\x00\x00\x2f\x2f\x2f\x2f\x2f\x2f\x2f\x2f\x2f\x2f\x2f\x2f\x2f\x2f\x2f",
    )
    message = WMbusMessage(raw_message)
    final_message = device.process_new_message(message)
    assert final_message.values[0].get("timestamp") is not None
    assert final_message.values[0].get("unit") == "°C"
    assert final_message.values[0].get("value") == 23.9


def test_process_message_v2():
    device = WeptechOMSv2(device_id="device_id", index=0)
    raw_message = IMSTMessage(
        endpoint_id=2,
        message_id=3,
        payload_length=46,
        with_timestamp_field=False,
        with_crc_field=False,
        with_rssi_field=False,
        payload=b"\x2e\x44\xb0\x5c\x74\x72\x00\x00\x02\x1b\x7a\xbf\x00\x00\x00\x2f\x2f\x0a\x66\x39\x02\x0a\xfb\x1a\x00\x05\x02\xfd\x97\x1d\x00\x00\x2f\x2f\x2f\x2f\x2f\x2f\x2f\x2f\x2f\x2f\x2f\x2f\x2f\x2f\x2f",
    )
    message = WMbusMessage(raw_message)
    final_message = device.process_new_message(message)
    assert final_message.values[0].get("timestamp") is not None
    assert final_message.values[0].get("unit") == "°C"
    assert final_message.values[0].get("value") == 23.9
    assert final_message.values[1].get("timestamp") is not None
    assert final_message.values[1].get("unit") == "%"
    assert final_message.values[1].get("value") == 50
