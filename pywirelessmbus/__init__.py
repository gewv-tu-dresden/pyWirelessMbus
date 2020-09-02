from pywirelessmbus.wmbus import WMbus
from loguru import logger

# disable logger on default because this is a lib
logger.disable(__name__)

__version__ = "1.2.0"
__all__ = ["WMbus"]
