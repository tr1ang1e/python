from .settings import Logfile
import logging
import logging.config
from logging.handlers import RotatingFileHandler


def carriage_return():
    print("\r")


def init_logger(logfile: Logfile):
    pass
    ''' formatter '''
    base_format = f"%(asctime)s.%(msecs)03d   | %(threadName)-11s  | %(filename)s:%(lineno)-4d  | %(levelname)-8s   >  %(message)s"
    timestamp_format = "%H:%M:%S"
    formatter = logging.Formatter(base_format, timestamp_format)
    ''' configure file logs '''
    file_handler = RotatingFileHandler(logfile.path, maxBytes=logfile.max_size, backupCount=logfile.backup_count)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    ''' configure console logs '''
    # probably not necessary
    # console_handler = logging.StreamHandler()
    # console_handler.setLevel(logging.INFO)
    # console_handler.setFormatter(formatter)

    ''' configure logger itself '''
    logger = logging.getLogger(logfile.name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    # logger.addHandler(console_handler)
    return logger