"""
Initialize logging defaults for Project.

"""
import os
import sys
import logging
import logging.config
import logging.handlers
from ruamel.yaml import YAML
import yaml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def configure_logging(logger_name):
    DEFAULT_LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
    }
    logging.config.dictConfig(DEFAULT_LOGGING)

    FORMATTER = "[%(asctime)s] [%(levelname)s] [%(name)s] [Module: %(module)s] [Function: %(funcName)s(), Line:%(lineno)s] [PID:%(process)d, " \
                "TID:%(thread)d] -> %(message)s"
    LOG_FILE = os.path.join(BASE_DIR, 'logs/DRY.logs')
    ERROR_LOG_FILE = os.path.join(BASE_DIR, 'logs/DRY_errors.logs')
    default_formatter = logging.Formatter(FORMATTER)

    def get_console_handler():
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(default_formatter)
        return console_handler

    def get_file_handler():
        log_handler = logging.handlers.TimedRotatingFileHandler(LOG_FILE, when='midnight', backupCount=100000)
        log_handler.setLevel(logging.INFO)
        log_handler.setFormatter(default_formatter)
        error_log_handler = logging.handlers.RotatingFileHandler(ERROR_LOG_FILE, maxBytes=5000, backupCount=100000)
        error_log_handler.setLevel(logging.ERROR)
        error_log_handler.setFormatter(default_formatter)
        return log_handler, error_log_handler

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)  # better to have too much logs than not enough
    logger.addHandler(get_console_handler())
    log_handler, error_log_handler = get_file_handler()
    logger.addHandler(log_handler)
    logger.addHandler(error_log_handler)
    # with this pattern, it's rarely necessary to propagate the error up to parent
    logger.propagate = False
    return logger


def setup_logging(default_path='config/logging.yaml', default_name="DRY"):
    if os.path.exists(default_path):
        with open(default_path, 'rt') as f:
            content = f.read()
            # log_config = yaml.safe_load(content)
            # config = yaml.safe_load(content)
            log_config = YAML(typ='safe')  # default, if not specified, is 'rt' (round-trip)
            log_config = log_config.load(content)
        logging.config.dictConfig(log_config)
        return None

    else:
        # set up logging
        logger = configure_logging(default_name)
        logger.info("Logging module configured by defaults from source code")
        return logger
