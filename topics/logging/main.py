"""
docs = https://docs.python.org/3/library/logging.html
full guide = https://coralogix.com/blog/python-logging-best-practices-tips/
review = https://habr.com/ru/post/513966/
"""


from logging import FileHandler
import logging.config
import logging.handlers
import time


def open_file_with_header(header_to_write: str):
    def do_when_open(function):
        def decorate(*args, **kwargs):
            file = function(*args, **kwargs)
            if not file.tell():  # RotatingFileHandler allows to open file only in 'append' mode if 'maxBytes' > 0
                file.write(header_to_write)
            return file
        return decorate
    return do_when_open


config = {
    "version": 1,                                                   # necessary field
    "formatters":
        {
            "myFormatter":
                {
                    "format": "%(asctime)s [%(levelname)s] %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                }
        },
    "handlers":
        {
            "myHandler":
                {
                    "class": "rotator.RotatingFileHandler",
                    "formatter": "myFormatter",
                    "filename": "myRotationLogs.txt",
                    "mode": "a",                                    # hardcoded "a" in source for RotatingFileHandler
                    "delay": False,
                    "level": "DEBUG",                               # don't use NOTSET (leads to default level)
                    "maxBytes": 4096,
                    "backupCount": 3,
                }
        },
    "loggers":
        {
            "myLogger":
                {
                    "handlers": ["myHandler"],
                    "level": "DEBUG"
                }
        },
}

# replace default open function of base class FileHandler with customized one
# must be done before getting logger
header = "CustomizedHeader"
temp = FileHandler._open
FileHandler._open = open_file_with_header(header)(FileHandler._open)

logging.config.dictConfig(config)
myLogger = logging.getLogger("myLogger")

# restore default open function of base class FileHandler (to avoid using while creating other loggers)
FileHandler._open = temp

# replace default open function of logger instance (to use for opening new files while rotating)
# this operation better with 'handler = RotatingFileHandler(...)'  >>  'handler._open = open_file_with_header(...)(...)'
# (to avoid excess actions and validations)
if len(myLogger.handlers) == 1:
    myLogger.handlers[0]._open = open_file_with_header(header)(myLogger.handlers[0]._open)

i = 0
while True:
    time.sleep(0.02)
    myLogger.warning("_SUCCESS_{}".format(i))
    i += 1
