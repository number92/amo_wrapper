import datetime
import logging
import os
from .config import BASE_DIR

log_format = "%(levelname)s : %(asctime)s - %(module)s/%(funcName)s - %(message)s"

current_date = datetime.datetime.now().strftime("%Y-%m-%d")


def get_logger(module):
    formatter = logging.Formatter(log_format)  # "%(asctime)s %(levelname)s %(message)s"
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    file_handler = logging.FileHandler(os.path.join(BASE_DIR, "logs", f"{current_date}.log"))
    file_handler.setFormatter(formatter)

    custom_logger = logging.getLogger(module)
    custom_logger.setLevel(logging.DEBUG)

    custom_logger.addHandler(handler)
    custom_logger.addHandler(file_handler)

    return custom_logger
