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

    - bnc.py:handle_price_msg - exceptions handling
    - trader.py:
        class Demo: trade()
    - account.py:
        api: get_placed_orders
        api: __update_account_data
    - decide which information should be permanently shown if any

"""
import traceback
from time import sleep

from modules import Account
from modules import BNCAttention, BNCCritical
from modules import Price
from modules import Settings
from modules import Demo2
from modules import parse_arguments


"""
    There is no way to change callback signature, and therefore 
    the global storage of 'class Trader' instances should be used
"""
traders = list()


def handle_price_msg(msg):
    """
        Callback function: just iterates over
        all registered accounts and calls trade
    """
    global traders
    try:
        for tr in traders:
            tr.trade(msg)
    except Exception as e:
        raise e


if __name__ == "__main__":
    btc = None
    account = None
    price = None
    args = parse_arguments()

    try:
        settings = Settings("./settings", args)

        """
            All 'Account' and 'Trader' instances must be created 
            before Price one, because callback, used by Price class, 
            involves 'Trader' class to proceed business logic
        """

        # Account
        account = Account(settings.api_demo, settings.recv_window, settings.account_log)
        account.get_balance()

        # Trader
        # trader = Demo2(settings.trader_log['demo2'])
        # trader.add_account(account)
        # traders.append(trader)

        """
            Price class is responsible for 
                - getting data using WebSocket connection
                - calling callback function for new data
                
            Executed in parallel thread
        """

        # price = Price(settings.price_log)
        # price.start_ticker("BTCUSDT", handle_price_msg)
        # sleep(20)
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
    except Exception as ex:
        print("Unknown EXCEPTION type raised")
        ex_string = traceback.format_exc()
        print(ex_string)
        account.logger.error(type(ex))      # TODO: temporarily, get clear output ...
        account.logger.error(ex)            # TODO: ... of unspecified exceptions
        # if price is not None:
        #    price.stop()
