"""
Initialize logging defaults for Project.

"""
import os
import sys
import logging
import logging.config
import logging.handlers
from utils.box import load_from_yaml, load_from_json, to_json, to_yaml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def configure_logging(logger_name):
    DEFAULT_LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
    }
    logging.config.dictConfig(DEFAULT_LOGGING)

    FORMATTER = "[%(asctime)s] [%(levelname)s] [%(name)s] [Module: %(module)s] [Function: %(funcName)s(), Line:%(lineno)s] [PID:%(process)d," \
                "TID:%(thread)d] -> %(message)s"  #MR2

    default_formatter = logging.Formatter(FORMATTER)

    def get_console_handler():
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(default_formatter)
        console_handler.setLevel(logging.DEBUG)  # better to have too much logs than not enough
        return console_handler

    def get_error_console_handler():
        error_console_handler = logging.StreamHandler(sys.stderr)
        error_console_handler.setFormatter(default_formatter)
        error_console_handler.setLevel(logging.ERROR)
        return error_console_handler

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)  # better to have too much logs than not enough
    logger.addHandler(get_console_handler())
    logger.addHandler(get_error_console_handler())
    # with this pattern, it's rarely necessary to propagate the error up to parent
    logger.propagate = False
    return logger


def setup_logging(path='config/logging.yaml', name="DRY"):
    if os.path.exists(path):
        log_config = load_from_yaml(filename=path)
        logging.config.dictConfig(log_config)
        return None

    else:
        # set up logging
        logger = configure_logging(name)
        logger.info("Logging module configured by defaults from source code")
        return logger
