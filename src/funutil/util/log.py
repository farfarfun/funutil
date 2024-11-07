import logging
from functools import cache


@cache
def get_logger(name="default", level=logging.INFO, formatter=None, handler=None):
    formatter = formatter or "%(asctime)s %(name)s %(levelname)s [%(filename)s - %(lineno)d - %(funcName)s] %(message)s"
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        logger.info(f"logger={name} is already configured")
        return logger
    if handler is None:
        handler = logging.StreamHandler()
        handler.setLevel(level=level)
        handler.setFormatter(logging.Formatter(formatter))
    logger.addHandler(handler)
    logger.setLevel(level=level)

    logger.info(
        f"init logger with name={name} and level={level}",
    )
    return logger


def getLogger(
    name="default",
    level=logging.INFO,
    formatter=None,
    handler=None,
):
    return get_logger(name, level=level, formatter=formatter, handler=handler)
