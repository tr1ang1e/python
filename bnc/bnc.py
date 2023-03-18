"""
TODO:
    - decide which information should be permanently shown if any
    - implement multithread logic
    - API:
        - get historical data
    - algorythm
    - implement exceptions
"""


from modules import Logfile, Api, Settings
from modules import carriage_return, init_logger
from modules import Order, Account
from modules import Price


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
        account.get_balance()

        # executed in parallel thread
        # price = Price()
        # price.start_ticker("BTCUSDT", handle_price_msg)
        # sleep(4)
        # price.stop()

    except Exception as e:
        print(e)
        if price:
            # price.stop()
            pass
