import serial
import serial_asyncio
from serial_asyncio import SerialTransport
import asyncio
import logging
from dataclasses import dataclass
from wmbus.exceptions import InvalidMessageLength
from wmbus.utils import Message
from types import MethodType

from typing import Callable, Any, Optional


logger = logging.getLogger(__name__)

# CONTANTS
NOOP = lambda *args: None
START_OF_FRAME = b"\xa5"

# Endpoint IDs
DEVMGMT_ID = 0x01
RADIOLINK_ID = 0x02
RADIOLINKTEST_ID = 0x03
HWTEST_ID = 0x04

# Device managment message ids
DEVMGMT_MSG_PING_REQ = 0x01
DEVMGMT_MSG_PING_RSP = 0x02


# Radiolink messages
RADIOLINK_MSG_WMBUSMSG_REQ = 0x01
RADIOLINK_MSG_WMBUSMSG_RSP = 0x02
RADIOLINK_MSG_WMBUSMSG_IND = 0x03
RADIOLINK_MSG_DATA_REQ = 0x04
RADIOLINK_MSG_DATA_RSP = 0x05


RADIOLINK_MSG_START_REQ = 0x06
RADIOLINK_MSG_START_RSP = 0x07
RADIOLINK_MSG_STOP_REQ = 0x08
RADIOLINK_MSG_STOP_RSP = 0x09
RADIOLINK_MSG_STATUS_IND = 0x0


@dataclass
class MessageProtocol(asyncio.Protocol):
    transport = None
    on_message: Callable[[Any, Message], None] = NOOP

    def connection_made(self, transport: SerialTransport):
        self.transport = transport
        logger.info("Serialport opened")
        # transport.serial.rts = False  # You can manipulate Serial object via transport
        transport.write(b"\xa5\x01\x01\x00")  # Write serial data via transport

    def data_received(self, data):
        logger.debug("data received %s", repr(data))
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
        logger.debug("Receive new message: %s", data.hex())
        control_field = data[1] >> 4
        message = Message(
            endpoint_id=data[1] & 0xF,
            message_id=data[2],
            payload_length=int(data[3]),
            with_timestamp_field=control_field & 0x2 > 0,
            with_rssi_field=control_field & 0x4 > 0,
            with_crc_Field=control_field & 0x8 > 0,
        )
        message.payload = data[4 : 4 + int(message.payload_length)]

        crc = None
        rssi = None
        timestamp = None

        logging.debug("Receive raw message: %s", data.hex())
        logging.debug("Endpoint ID: %s", message.endpoint_id)
        logging.debug("Message ID: %s", message.message_id)
        logging.debug("Payload Length: %s", message.payload_length)
        logging.debug("Payload: %s", message.payload.hex())

        if message.with_crc_Field:
            message.crc = data[-2:]
            logging.debug("CRC: %s", message.crc)
            # TODO: add CRC Check

        if message.with_rssi_field:
            message.rssi = data[
                4 + message.payload_length + message.with_timestamp_field * 4
            ]
            logging.debug("RSSI: %s", message.rssi)

        if message.with_timestamp_field:
            message.timestamp = data[
                4 + message.payload_length : 4 + message.payload_length + 4
            ]
            logging.debug("Timestamp: %s", message.timestamp)

        self.on_message(message)


@dataclass
class IM871A_USB:
    path: str
    baudrate: int = 57600
    on_new_message: Callable[[Any, bytes], None] = NOOP
    transport: Optional[SerialTransport] = None
    message_protocol: Optional[MessageProtocol] = None
    on_radio_message: Callable[[Any, Message], None] = NOOP

    def __post_init__(self):
        self._loop = asyncio.get_event_loop()
        self._serial_coro = serial_asyncio.create_serial_connection(
            self._loop, MessageProtocol, self.path, baudrate=self.baudrate, timeout=0.1
        )
        self.keepalive = False

    def stop_watch(self):
        logger.info("Stop watching input from wMbus stick iM871a.")
        self.keepalive = False

    def watch(self):
        logger.info("Start to watch input from wMbus stick iM871a.")
        [self.transport, self.message_protocol] = self._loop.run_until_complete(
            self._serial_coro
        )

        # Register events
        self.message_protocol.on_message = self.process_message

    def process_message(self, message: Message):
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

    def process_radio_message(self, message: Message):
        self.on_radio_message(message)

    def process_devicemanagment_message(self, message: Message):
        if message.message_id == DEVMGMT_MSG_PING_RSP:
            logger.info("Receive a valid ping response from IM871A")
        else:
            logger.warning("Received devicemanagment message is not implemented yet.")

    def send_message(self, message: bytes):
        if self.transport is None:
            logger.warning("No transport initiliazed. Can't send the message.")
            return

        logger.debug("Send message to RF Module: " + str(message))
        self.transport.write(message)

    def ping(self):
        logger.info("Send Ping Command to RF Module")
        self.send_message(b"\xa5\x01\x01\x00")
