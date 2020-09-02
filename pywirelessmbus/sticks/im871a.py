import serial_asyncio
from serial_asyncio import SerialTransport
import asyncio
from loguru import logger
from dataclasses import dataclass
from pywirelessmbus.utils import IMSTMessage
from pywirelessmbus.utils.utils import NOOP

from typing import Callable, Any, Optional


# CONTANTS
START_OF_FRAME = b"\xa5"
ZERO_LENGTH = b"\x00"

# Link Mode Mapping
LINK_MODE = {
    0: "S1",
    1: "S1-m",
    2: "S2",
    3: "T1",
    4: "T2",
    5: "R2",
    6: "C1, Telegram Format A",
    7: "C1, Telegram Format B",
    8: "C2, Telegram Format A",
    9: "C2, Telegram Format B",
}

# RF Channel Mapping
RF_CHANNEL = {
    1: "868.09 MHz (R-Mode)",
    2: "868.15 MHz (R-Mode)",
    3: "868.21 MHz (R-Mode)",
    4: "868.27 MHz (R-Mode)",
    5: "868.33 MHz (R-Mode)",
    6: "868.39 MHz (R-Mode)",
    7: "868.45 MHz (R-Mode)",
    8: "868.51 MHz (R-Mode)",
    9: "868.57 MHz (R-Mode)",
    10: "868.30 MHz (S-Mode)",
    11: "868.09 MHz (T-Mode)",
}

# Radio Power Level
RADIO_POWER = {
    0: "-8 dBm",
    1: "-5 dBm",
    2: "-2 dBm",
    3: "1 dBm",
    4: "4 dBm",
    5: "7 dBm",
    6: "10 dBm",
    7: "14 dBm",
}

# Endpoint IDs
DEVMGMT_ID = 1
RADIOLINK_ID = 2
RADIOLINKTEST_ID = 3
HWTEST_ID = 4

# Device managment message ids
DEVMGMT_MSG_PING_REQ = b"\x01"
DEVMGMT_MSG_PING_RSP = b"\x02"
DEVMGMT_MSG_SET_CONFIG_REQ = b"\x03"
DEVMGMT_MSG_SET_CONFIG_RES = b"\x04"
DEVMGMT_MSG_GET_CONFIG_REQ = b"\x05"
DEVMGMT_MSG_GET_CONFIG_RES = b"\x06"
DEVMGMT_MSG_RESET_REQ = b"\x07"
DEVMGMT_MSG_RESET_RES = b"\x08"
DEVMGMT_MSG_FACTORY_RESET_REQ = b"\x09"
DEVMGMT_MSG_FACTORY_RESET_RES = b"\x0A"
DEVMGMT_MSG_GET_DEVICEINFO_REQ = b"\x0F"
DEVMGMT_MSG_GET_DEVICEINFO_RES = b"\x10"
DEVMGMT_MSG_ENABLE_AES_ENCKEY_REQ = b"\x23"
DEVMGMT_MSG_ENABLE_AES_ENCKEY_RSP = b"\x24"
DEVMGMT_MSG_SET_AES_DECKEY_REQ = b"\x25"
DEVMGMT_MSG_SET_AES_DECKEY_RSP = b"\x26"
DEVMGMT_MSG_AES_DEC_ERROR_IND = b"\x27"

# Radiolink messages
RADIOLINK_MSG_WMBUSMSG_REQ = b"\x01"
RADIOLINK_MSG_WMBUSMSG_RSP = b"\x02"
RADIOLINK_MSG_WMBUSMSG_IND = b"\x03"
RADIOLINK_MSG_DATA_REQ = b"\x04"
RADIOLINK_MSG_DATA_RSP = b"\x05"

# Radiolinktest messages
RADIOLINKTEST_MSG_START_REQ = b"\x01"
RADIOLINKTEST_MSG_START_RSP = b"\x02"
RADIOLINKTEST_MSG_STOP_REQ = b"\x03"
RADIOLINKTEST_MSG_STOP_RSP = b"\x04"
RADIOLINKTEST_MSG_STATUS_IND = b"\x07"

# Hardware Test Messages
HWTEST_MSG_RADIOTEST_REQ = b"\x01"
HWTEST_MSG_RADIOTEST_REQ = b"\x02"


@dataclass
class MessageProtocol(asyncio.Protocol):
    transport = None
    on_message: Callable[[Any, IMSTMessage], None] = NOOP

    def connection_made(self, transport: SerialTransport):
        self.transport = transport
        logger.info("Serialport opened")

    def data_received(self, data):
        logger.debug("data received {}", repr(data))
        if data.startswith(START_OF_FRAME):
            asyncio.create_task(self.decode_message(data))

    def connection_lost(self, exc):
        logger.info("Serialport closed")
        self.transport.loop.stop()

    def pause_writing(self):
        logger.info("pause writing")
        logger.info(self.transport.get_write_buffer_size())

    def resume_writing(self):
        logger.info(self.transport.get_write_buffer_size())
        logger.info("resume writing")

    def write_message(self, message):
        self.transport.write(message)

    async def decode_message(self, data: bytes):
        logger.debug("Receive new message: {}", data.hex())
        control_field = data[1] >> 4
        message = IMSTMessage(
            endpoint_id=data[1] & 0xF,
            message_id=data[2:3],
            payload_length=int(data[3]),
            with_timestamp_field=control_field & 0x2 > 0,
            with_rssi_field=control_field & 0x4 > 0,
            with_crc_field=control_field & 0x8 > 0,
        )
        message.payload = data[3 : 4 + int(message.payload_length)]

        logger.debug("Receive raw message: {}", data.hex())
        logger.debug("Endpoint ID: {}", message.endpoint_id)
        logger.debug("Message ID: {}", message.message_id)
        logger.debug("Payload Length: {}", message.payload_length)
        logger.debug("Payload: {}", message.payload.hex())

        if message.with_crc_field:
            message.crc = data[-2:]
            logger.debug("CRC: {}", message.crc)
            # TODO: add CRC Check

        if message.with_rssi_field:
            message.rssi = data[
                4 + message.payload_length + message.with_timestamp_field * 4
            ]
            logger.debug("RSSI: {}", message.rssi)

        if message.with_timestamp_field:
            message.timestamp = data[
                4 + message.payload_length : 4 + message.payload_length + 4
            ]
            logger.debug("Timestamp: {}", message.timestamp)

        self.on_message(message)


@dataclass
class IM871A_USB:
    path: str
    baudrate: int = 57600
    on_new_message: Callable[[Any, bytes], None] = NOOP
    transport: Optional[SerialTransport] = None
    message_protocol: Optional[MessageProtocol] = None
    on_radio_message: Callable[[Any, IMSTMessage], None] = NOOP

    def __post_init__(self):
        self._device_mode = None
        self._link_mode = None
        self._manufacturer_id = None
        self._device_id = None
        self._auto_rssi_attachment = None
        self._auto_timestamp_attachment = None
        self._loop = asyncio.get_event_loop()
        self._serial_coro = serial_asyncio.create_serial_connection(
            self._loop, MessageProtocol, self.path, baudrate=self.baudrate, timeout=0.1
        )
        self.keepalive = False

    @property
    def device_mode(self):
        return self._device_mode

    @property
    def link_mode(self) -> int:
        if self._link_mode is None:
            return -1
        return self._link_mode

    @link_mode.setter
    def link_mode(self, new_link_mode: str):
        logger.info("Set stick on link mode {}.", new_link_mode)
        inv_link_mapping = {v: k for k, v in LINK_MODE.items()}

        link_mode_code = inv_link_mapping.get(new_link_mode)

        if link_mode_code is None:
            logger.error(
                "Request a unknown link mode. Possible link modes are : {}",
                ", ".join(LINK_MODE.values()),
            )
            return

        self.set_device_configuration(b"\x02" + bytes([link_mode_code]) + b"\x00")

    @property
    def manufacturer_id(self):
        return self._manufacturer_id

    @property
    def device_id(self):
        return self._device_id

    @property
    def auto_rssi_attachment(self):
        return self._auto_rssi_attachment

    @auto_rssi_attachment.setter
    def auto_rssi_attachment(self, activate: bool):
        logger.info("Set RSSI Attachment to {}.", activate)

        if activate is None or not isinstance(activate, bool):
            logger.error("Tried to set with non bool param. Possible is True and False")
            return

        self.set_device_configuration(b"\x00\x10" + bytes([activate]))

    @property
    def auto_timestamp_attachment(self):
        return self._auto_timestamp_attachment

    @auto_timestamp_attachment.setter
    def auto_timestamp_attachment(self, activate: bool):
        logger.info("Set Timestamp Attachment to {}.", activate)

        if activate is None or not isinstance(activate, bool):
            logger.error("Tried to set with non bool param. Possible is True and False")
            return

        self.set_device_configuration(b"\x00\x20" + bytes([activate]))

    def stop_watch(self):
        logger.info("Stop watching input from pywirelessmbus stick iM871a.")
        self.keepalive = False

    async def watch(self):
        logger.info("Start to watch input from pywirelessmbus stick iM871a.")
        [self.transport, self.message_protocol] = await self._serial_coro

        # Register events
        self.message_protocol.on_message = self.process_message

        # Load config from stick
        self.get_device_configuration()

    def process_message(self, message: IMSTMessage):
        if message.endpoint_id == RADIOLINK_ID:
            self.process_radio_message(message)
        elif message.endpoint_id == DEVMGMT_ID:
            self.process_devicemanagment_message(message)
        elif message.endpoint_id == RADIOLINKTEST_ID:
            # TODO: Implement Radiolink Test Decoder
            logger.warning("Decoder for radiolink test messages not implemented yet.")
        elif message.endpoint_id == HWTEST_ID:
            # TODO: Implement Hardware Test Decoder
            logger.warning("Decoder for hardware test messages not implemented yet.")
        else:
            logger.warning("Receive message with unknown endpoint id.")

    def process_radio_message(self, message: IMSTMessage):
        self.on_radio_message(message)

    def process_devicemanagment_message(self, message: IMSTMessage):
        if message.message_id == DEVMGMT_MSG_PING_RSP:
            logger.info("Receive a valid ping response from IM871A")
        elif message.message_id == DEVMGMT_MSG_RESET_RES:
            logger.info("Receive a valid reset response. Stick will reset soon.")
        elif message.message_id == DEVMGMT_MSG_GET_DEVICEINFO_RES:
            self.process_device_info_message(message)
        elif message.message_id == DEVMGMT_MSG_GET_CONFIG_RES:
            self.process_device_config_message(message)
        elif message.message_id == DEVMGMT_MSG_SET_CONFIG_RES:
            logger.info(
                "Receive a valid config set response. Reload config from device."
            )
            self.get_device_configuration()
        elif message.message_id == DEVMGMT_MSG_SET_AES_DECKEY_RSP:
            if message.payload is None:
                logger.error("Receive invalid response for setting AES Key.")
                return

            status = bool(message.payload[1])
            logger.info(
                "Set the AES Key. Operation {}",
                "was successful" if status else "failed",
            )
        elif message.message_id == DEVMGMT_MSG_ENABLE_AES_ENCKEY_RSP:
            if message.payload is None:
                logger.error(
                    "Receive invalid response for enable/disable AES encryption."
                )
                return

            status = bool(message.payload[1])
            logger.info(
                "Activating/Deactivating the AES Encrytion. Operation {}",
                "was successful" if status else "failed",
            )
        elif message.message_id == DEVMGMT_MSG_AES_DEC_ERROR_IND:
            logger.warning(
                "Failed to decrypt the message a device. Maybe the wrong or no key is stored."
            )
            if message.payload is not None:
                logger.info("Device Header: {}", message.payload.hex())
        elif message.message_id == DEVMGMT_MSG_FACTORY_RESET_RES:
            if message.payload is None:
                logger.error("Receive invalid response for factory reset.")
                return

            status = bool(message.payload[1])
            logger.info(
                "Requested the factory reset. Operation {}",
                "was successful" if status else "failed",
            )
        else:
            logger.warning("Received devicemanagment message is not implemented yet.")

    def process_device_info_message(self, info_message: IMSTMessage):
        if info_message.payload is None:
            logger.warning("Receive device info message with no content.")
            return

        logger.info("Receive device infos from stick:")
        logger.info("Module Type: {}", info_message.payload[1:2].hex())

        self._device_mode = info_message.payload[2:3].hex()
        logger.info("Device Mode: {}", self.device_mode)

        logger.info("Firmware: {}", info_message.payload[3:4].hex())
        logger.info("HCI Protocol version: {}", info_message.payload[4:5].hex())
        logger.info("Device ID: {}", info_message.payload[5:9].hex())

    def process_device_config_message(self, config_message: IMSTMessage):
        logger.info("Receive device config from stick:")
        if config_message.payload is None:
            logger.warning("Receive device config with no content.")
            return

        information_indicator_flag = config_message.payload[1]
        offset = 2

        """
        Device Mode
        """
        if information_indicator_flag & 1:
            self._device_mode = config_message.payload[offset]
            logger.info("Device Mode: {}", "Meter" if self.device_mode else "Other")
            offset += 1

        """
        Link Mode
        """
        if information_indicator_flag & 2:
            self._link_mode = config_message.payload[offset]
            logger.info("Link Mode: {}", LINK_MODE[self.link_mode])
            offset += 1

        """
        WM-Bus C Field
        """
        if information_indicator_flag & 4:
            logger.info(
                "WM-Bus C Field: {}", config_message.payload[offset : offset + 1].hex()
            )
            offset += 1

        """
        Manufacturer ID
        """
        if information_indicator_flag & 8:
            self._manufacturer_id = config_message.payload[offset : offset + 2][
                ::-1
            ].hex()
            logger.info("WM-Bus Manufacturer ID: {}", self._manufacturer_id)
            offset += 2

        """
        Device ID
        """
        if information_indicator_flag & 16:
            self._device_id = config_message.payload[offset : offset + 4][::-1].hex()
            logger.info("WM-Bus Device ID: {}", self.device_id)
            offset += 4

        """
        WM-Bus Version
        """
        if information_indicator_flag & 32:
            logger.info(
                "WM-Bus Version: {}", config_message.payload[offset : offset + 1].hex()
            )
            offset += 1

        """
        WM-Bus Device Type
        """
        if information_indicator_flag & 64:
            logger.info(
                "WM-Bus Device Type: {}",
                config_message.payload[offset : offset + 1].hex(),
            )
            offset += 1

        """
        Radio Channel
        """
        if information_indicator_flag & 128:
            logger.info("Radio Channel: {}", RF_CHANNEL[config_message.payload[offset]])
            offset += 1

        information_indicator_flag_2 = config_message.payload[offset]
        offset += 1

        """
        Radio Power Level
        """
        if information_indicator_flag_2 & 1:
            logger.info(
                "Radio Power Level: {}", RADIO_POWER[config_message.payload[offset]]
            )
            offset += 1

        """
        Radio Data Rate
        """
        if information_indicator_flag_2 & 2:
            logger.info(
                "Radio Data Rate: {}", config_message.payload[offset : offset + 1].hex()
            )
            offset += 1

        """
        Radio Rx-Window
        """
        if information_indicator_flag_2 & 4:
            logger.info("Radio Rx Window: {} ms", config_message.payload[offset])
            offset += 1

        """
        Auto Power Saving
        """
        if information_indicator_flag_2 & 8:
            logger.info("Auto Power Saving: {}", bool(config_message.payload[offset]))
            offset += 1

        """
        Auto RSSI Attachment
        """
        if information_indicator_flag_2 & 16:
            self._auto_rssi_attachment = bool(config_message.payload[offset])
            logger.info("Auto RSSI Attachment: {}", self.auto_rssi_attachment)
            offset += 1

        """
        Auto Timestamp Attachment
        """
        if information_indicator_flag_2 & 32:
            self._auto_timestamp_attachment = bool(config_message.payload[offset])
            logger.info("Auto Timestamp Attachment: {}", self.auto_timestamp_attachment)
            offset += 1

        """
        LED Control
        """
        if information_indicator_flag_2 & 64:
            logger.info("LED Control: {}", bool(config_message.payload[offset]))
            offset += 1

        """
        RTC Control
        """
        if information_indicator_flag_2 & 128:
            logger.info("RTC Control: {}", bool(config_message.payload[offset]))
            offset += 1

    def send_message(self, message: bytes):
        if self.transport is None:
            logger.warning("No transport initiliazed. Can't send the message.")
            return

        logger.debug("Send message to RF Module: " + str(message))
        self.transport.write(message)

    def ping(self):
        logger.info("Send Ping Command to RF Module")
        payload_length = b"\x00"
        control_field = bytes([(0 << 4) + DEVMGMT_ID])

        self.send_message(
            START_OF_FRAME + control_field + DEVMGMT_MSG_PING_REQ + payload_length
        )

    def reset(self):
        logger.info("Request Reset")
        payload_length = b"\x00"
        control_field = bytes([(0 << 4) + DEVMGMT_ID])

        self.send_message(
            START_OF_FRAME + control_field + DEVMGMT_MSG_RESET_REQ + payload_length
        )

    def factory_reset(self, reboot: bool = False):
        logger.info("Request factory reset")
        payload_length = b"\x01"
        reboot_flag = b"\x01" if reboot else b"\x00"
        control_field = bytes([(0 << 4) + DEVMGMT_ID])

        self.send_message(
            START_OF_FRAME
            + control_field
            + DEVMGMT_MSG_FACTORY_RESET_REQ
            + payload_length
            + reboot_flag
        )

    def get_device_infos(self):
        logger.info("Send device info request")
        payload_length = b"\x00"
        control_field = bytes([(0 << 4) + DEVMGMT_ID])

        self.send_message(
            START_OF_FRAME
            + control_field
            + DEVMGMT_MSG_GET_DEVICEINFO_REQ
            + payload_length
        )

    def get_device_configuration(self):
        logger.info("Send device configuration request")
        payload_length = b"\x00"
        control_field = bytes([(0 << 4) + DEVMGMT_ID])

        self.send_message(
            START_OF_FRAME + control_field + DEVMGMT_MSG_GET_CONFIG_REQ + payload_length
        )

    def set_device_configuration(self, configuration: bytes, persistant: bool = False):
        logger.info("Set device configuration")
        payload_length = bytes([len(configuration) + 1])
        control_field = bytes([(0 << 4) + DEVMGMT_ID])
        # store persistant
        nvm_flag = b"\x01" if persistant else b"\x00"

        self.send_message(
            START_OF_FRAME
            + control_field
            + DEVMGMT_MSG_SET_CONFIG_REQ
            + payload_length
            + nvm_flag
            + configuration
        )

    def _change_aes_encryption(self, enable: bool, persistant: bool = False):
        logger.info("{} the aes encryption.", "Enable " if enable else "Disable ")

        payload_length = b"\x02"
        control_field = bytes([(0 << 4) + DEVMGMT_ID])
        nvm_flag = b"\x01" if persistant else b"\x00"
        activation_flag = b"\x01" if enable else b"\x00"

        self.send_message(
            START_OF_FRAME
            + control_field
            + DEVMGMT_MSG_ENABLE_AES_ENCKEY_REQ
            + payload_length
            + nvm_flag
            + activation_flag
        )

    def enable_aes_encryption(self, persistant: bool = False):
        self._change_aes_encryption(True, persistant)

    def disable_aes_encryption(self, persistant: bool = False):
        self._change_aes_encryption(False, persistant)

    def set_aes_decryption_key(self, table_index: int, device_id: str, key: bytes):
        """
        Set multiple keys for divices.
        The process activate the decryption. Resetable with factory reset.
        """
        logger.info(
            "Set decryption key for device {} on table position {}.",
            device_id,
            table_index,
        )

        payload_length = b"\x19"
        control_field = bytes([(0 << 4) + DEVMGMT_ID])

        self.send_message(
            START_OF_FRAME
            + control_field
            + DEVMGMT_MSG_SET_AES_DECKEY_REQ
            + payload_length
            + bytes([table_index])
            + bytes.fromhex(device_id)
            + key
        )
