# pyWMbus

This module can decode messages from wireless M-Bus devices. The messages must received from a usb-uart stick. At this moment only the [iM871A-USB from IMST](https://shop.imst.de/wireless-modules/usb-radio-products/10/im871a-usb-wireless-m-bus-usb-adapter-868-mhz) is usable. Maybe somebody can add a alternative.

On the device side pyWMbus reads the messages from the Temp/Hum Sensor [Munia from Weptech](https://www.weptech.de/en/wireless-m-bus/humidity-temperature-sensor-munia.html). The implemantation of the [EnergyCam from Q-loud] is planned.

## Installation

```
pipenv install
pipenv shell
python ./wmbus/wmbus.py
```

## Plans

- Add more devices
- Add setup.py
- Add tests
- Send messages
