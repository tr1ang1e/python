"""
TODO, long:

    1. simple trading logic
    2. convenient parameters setting:
        - money management
        - orders distance
    3. telegram notifications
    4. better multithread logic: split websocket callback and trading logic
    5. test on historical data
        - api: get historical data
        - class Tester
    6. reimplement in C

TODO, current (1. simple trading logic):

    - account.py:
        class Order implementation
        api: get_placed_orders
        api: __update_account_data
    - account.py: parce response for placed order
    - decide which information should be permanently shown if any
    - bnc.py:
        handle_price_msg:
            - except
            - implement trading logic
"""
import traceback

from modules import Account
from modules import BNCAttention, BNCCritical
from modules import Settings
from modules import parse_arguments, init_logger


handler_logger = None


def handle_price_msg(msg):
    """
        Main business logic function
    """
    try:
        print(msg["c"])   # "c" = last price
    except Exception as ex:
        pass


if __name__ == "__main__":
    btc = None
    price = None
    common_logger = None
    args = parse_arguments()

    try:
        settings = Settings("./settings", args.api)
        common_logger = init_logger(settings.account_log)

        # Account instance must be created before Price one, reason:
        # Account logger is used inside callback involved by Price streams
        account = Account(settings.api_demo, settings.recv_window, common_logger)
        common_logger = account.logger
        account.get_balance()

        # executed in parallel thread
        # price = Price(settings.price_log)
        # price.start_ticker("BTCUSDT", handle_price_msg)
        # sleep(4)
        # price.stop()

    except IOError as ex:
        print("Failed to get settings")
        ex_string = traceback.format_exc()
        print(ex_string)
    # BNCCritical doesn't require special handling,
    # due to no real account work wasn't started yet
    except (BNCAttention, BNCCritical) as ex:
        ex_string = traceback.format_exc()
        print(ex_string)
        common_logger.error(ex)
    except Exception as ex:
        print("Unknown EXCEPTION type raised")
        ex_string = traceback.format_exc()
        print(ex_string)
        common_logger.error(type(ex))
        common_logger.error(ex)
        # if price is not None:
        #    price.stop()
