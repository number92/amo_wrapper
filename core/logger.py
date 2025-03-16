import datetime
import logging
import os
from .config import BASE_DIR

log_format = "%(levelname)s : %(asctime)s - %(module)s/%(funcName)s - %(message)s"

current_mounth = datetime.datetime.now().strftime("%Y-%m")


def get_logger(module=__name__, level=logging.INFO):

    custom_logger = logging.getLogger(module)
    custom_logger.setLevel(level)

    if not custom_logger.handlers:

        formatter = logging.Formatter(log_format)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        custom_logger.addHandler(console_handler)

        file_handler = logging.FileHandler(os.path.join(BASE_DIR, "logs", f"{current_mounth}.log"))
        file_handler.setFormatter(formatter)
        custom_logger.addHandler(file_handler)

    return custom_logger
