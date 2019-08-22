from wmbus import WMbus
from time import sleep
import asyncio


def main():
    loop = asyncio.get_event_loop()
    wmbus = WMbus("IM871A_USB")
    wmbus.start()

    asyncio.run(asyncio.sleep(1))
    wmbus.stick.auto_timestamp_attachment = True

    asyncio.run(asyncio.sleep(1))
    wmbus.stick.auto_rssi_attachment = True

    loop.run_forever()
    loop.close()


if __name__ == "__main__":
    main()

