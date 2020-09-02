from pywirelessmbus.devices import Device
from pywirelessmbus.utils.message import WMbusMessage
from typing import Optional, Tuple
from loguru import logger

METER_TYPE = {1: "Oil", 2: "Energy (electricity)", 3: "Gas", 7: "Water", 15: "Unknown"}
UNITS = {0: "Wh", 2: "m3"}


class EnergyCam(Device):
    updated_at: Optional[float]
    meter_type: int

    def __init__(self, meter_type, *args, **kwargs):
        self.updated_at = None
        self.meter_type = meter_type

        super().__init__(*args, **kwargs)

    def process_new_message(self, message: WMbusMessage) -> WMbusMessage:
        offset = 0

        logger.info(
            "Got new message from {} meter with ID: {}",
            METER_TYPE[self.meter_type],
            self.id,
        )
        logger.debug("Raw Message: {}", message.raw.hex())

        decryption_check = message.raw[15:17]
        if decryption_check != b"\x2f\x2f":
            logger.debug("Decrytpion check: {}", decryption_check.hex())
            logger.error(
                "Receive a encrypted message. You should deactivate the encryption or set the AES Key for the device."
            )
            return message

        # Analyse DIF
        dif = message.raw[17:18]
        logger.debug("DIF: {}", dif.hex())
        extension, error_state = self.analyse_dif(dif)

        if error_state:
            logger.warn("Receive old value. Energy Cam failed to read new value.")

        if extension:
            logger.warn(
                "Receive multiple datainformation fields. Only single are supported. Ignore second field."
            )
            offset += 1

        # Analyse VIF
        vif = message.raw[18 + offset : 19 + offset]
        logger.debug("VIF: {}", vif.hex())
        extension, unit, exponent = self.analyse_vif(vif)

        if extension:
            logger.warn(
                "Receive multiple valueinformation fields. Only single are supported. Ignore second field."
            )
            offset += 1

        # Analyse Value Field
        raw_value = int.from_bytes(message.raw[19 + offset : 23 + offset], "little")
        logger.debug("Raw value: {}", raw_value)
        logger.debug("Exponent: {}", exponent)
        value = raw_value / 10 ** exponent

        logger.info("New value from energy cam {}:", self.id)
        logger.info("{}: {} {}", METER_TYPE[self.meter_type], value, unit)
        message.add_value(value=value, unit=unit)
        return message

    def analyse_dif(self, dif: bytes) -> Tuple[bool, bool]:
        dec_value = int.from_bytes(dif, "little")
        extension = bool(dec_value & 128)
        error_state = (dec_value & 48) == 48

        return extension, error_state

    def analyse_vif(self, vif: bytes) -> Tuple[bool, str, int]:
        dec_value = int.from_bytes(vif, "little")
        extension = bool(dec_value & 128)
        try:
            logger.debug("Raw unit code: {}", (dec_value & 120) >> 3)
            unit = UNITS[(dec_value & 120) >> 3]
        except KeyError:
            logger.warn("Receive unknown unit from energy cam. Set 'unset'")
            unit = "unset"

        exponent = dec_value & 7

        return extension, unit, exponent
