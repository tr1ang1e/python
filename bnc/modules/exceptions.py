from enum import Enum


bnc_lib_exc_str = "Binance lib exception:"


class BNCExceptions(Enum):
    UNSPECIFIED = -1
    # '0' code is not used due to it usually indicates success
    API_ACCESS = 1
    API_PERMISSIONS = 2
    TICKER_START = 3
    PLACE_ORDER = 4
    CANSEL_ORDER = 5
    INCORRECT_ARGS = 6
    GET_ORDERS = 7
    SYMBOL_INFO = 8


class BNCAttention(Exception):
    def __init__(self, error=BNCExceptions.UNSPECIFIED, message="BNCAttention"):
        self.error = error
        message = message + f" (internal error: {error})"
        super().__init__(message)


class BNCCritical(Exception):
    def __init__(self, error=BNCExceptions.UNSPECIFIED, message="BNCCritical"):
        self.error = error
        message = message + f" (internal error: {error})"
        super().__init__(message)

