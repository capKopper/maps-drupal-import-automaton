"""Logging class."""
import logging

from colorlog import ColoredFormatter


def configure():
    """Configure logger."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = ColoredFormatter(
                '%(asctime)s %(log_color)s(%(levelname)-s)%(reset)s: %(message)s ',
                datefmt='%Y-%m-%dT%H:%M:%S',
                log_colors={
                    'DEBUG':    'cyan',
                    'INFO':     'green',
                    'ERROR':    'red',
    })

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger
