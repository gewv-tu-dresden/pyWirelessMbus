from wmbus import WMbus
import asyncio


def test_init():
    wMbus = WMbus("IM871A_USB", path="/dev/ttyUSB0")

    asyncio.run(wMbus.start())
    wMbus.stick.ping()

    asyncio.sleep(1)

    wMbus.stop()


if __name__ == "__main__":
    test_init()
