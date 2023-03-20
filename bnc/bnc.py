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

    - account.py: add exceptions (+ migrate UNSPECIFIED to main)
    - account.py:
        api: get_placed_orders
        api: __update_account_data
        api: add retry loops to place and cancel methods
    - account.py: parce response for placed order
    - decide which information should be permanently shown if any
    - bnc.py:
        handle_price_msg: implement trading logic
        main: exceptions handle
            - except ...
            - add trace
"""


from modules import Account, Order
from modules import BNCAttention, BNCCritical, BNCExceptions
from modules import Price
from modules import Api, Logfile, Settings
from modules import carriage_return, init_logger


def handle_price_msg(msg):
    """
        Main business logic function
    """
    print(msg["c"])   # "c" = last price
    return


if __name__ == "__main__":
    btc = None
    price = None
    try:
        settings = Settings("./settings")
        account = Account(settings.api_demo, settings.account_log)
        # account.get_balance()

        # executed in parallel thread
        # price = Price(settings.price_log)
        # price.start_ticker("BTCUSDT", handle_price_msg)
        # sleep(4)
        # price.stop()

    except BNCAttention as ex:
        print(ex)

    except Exception as ex:
        print(type(ex))
        print(ex)
        if price:
            # price.stop()
            pass
