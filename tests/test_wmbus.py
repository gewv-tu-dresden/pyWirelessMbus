from wmbus import WMbus


def test_init():
    wMbus = WMbus("IM871A_USB", path="/dev/ttyUSB0")

    assert type(wMbus) == WMbus
