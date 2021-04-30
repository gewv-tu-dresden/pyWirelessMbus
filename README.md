# pyWirelessMbus

This module can decode messages from wireless M-Bus devices. The messages must received from a usb-uart stick. At this moment only the [iM871A-USB from IMST](https://shop.imst.de/wireless-modules/usb-radio-products/10/im871a-usb-wireless-m-bus-usb-adapter-868-mhz) is usable. Maybe somebody can add a alternative.

On the device side pyWirelessMbus reads the messages from the Temp/Hum Sensor [Munia from Weptech](https://www.weptech.de/en/wireless-m-bus/humidity-temperature-sensor-munia.html) and the [EnergyCam from Q-loud](https://www.q-loud.de/energycam).

## Requirements

Python >= 3.8

## Installation

```
pip install pywirelessmbus
```

## Development

For testing you can install all deps and start the module with that commands.

```
poetry install
poetry shell
python examples/monitor.py
```

## Plans

- Add more devices
- Add tests
- Send messages
