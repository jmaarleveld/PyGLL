import logging
import sys


ROOT = 'Orion'

formatter = logging.Formatter('[{name}][{asctime}][{levelname}]: {msg}',
                              style='{')
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)

global_log = logging.getLogger(ROOT)
global_log.addHandler(handler)
global_log.setLevel(logging.DEBUG)


def get_logger(name: str) -> logging.Logger:
    full_name = f'{ROOT}.{name}'
    return logging.getLogger(full_name)
