"""
TODO:
    - decide which information should be permanently shown if any
    - implement multithread logic
    - API:
        - get historical data
    - algorythm
    - implement exceptions
"""


from modules import Account, Order
from modules import BNCAttention, BNCCritical, BNCExceptions
from modules import Price
from modules import Api, Logfile, Settings
from modules import carriage_return, init_logger


def handle_price_msg(msg):
    """
        main business logic function
        TODO: implement two thread logic
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
