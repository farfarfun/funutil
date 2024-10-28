import logging

from .time import RunTimer
from .util import deep_get

__all__ = ["RunTimer", "deep_get"]


logger = logging.getLogger("funutil")

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)
logger.setLevel(level=logging.INFO)
