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
    - account.py: how does Client.place_order() with stop-limit order work?
    - trader.py: trade()
    - decide which information should be permanently shown if any

"""
import traceback
from time import sleep

from modules import Account, Order
from modules import BNCAttention, BNCCritical
from modules import Price
from modules import Settings
from modules import Eleven
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
        # TODO: all important exceptions are here
        print("EXCEPTION in HANDLE_PRICE_MSG()")
        print(e)
        print(traceback.format_exc())


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
        order = Order('BTCUSDT', unique_id='KLH3LhgUQXs625Bt6k89kU')
        # account.cancel_order(order)
        account.get_balance()

        # Trader
        name = 'eleven'
        trader = Eleven(settings.trader_log[name], settings.traders[name])
        trader.add_account(account)
        traders.append(trader)

        """
            Price class is responsible for 
                - getting data using WebSocket connection
                - calling callback function for new data
                
            Executed in parallel thread
        """

        flag = 0
        if flag:
            price = Price(settings.price_log)
            price.start_ticker("BTCUSDT", handle_price_msg)
            sleep(3)
            price.stop()

        # debug
        for o in account.get_placed_orders('BTCUSDT'):
            print(o)

        """
            This thread is used to initialization and to
            starting the work. So no exceptions require
            handling due to business logic thread
            is started by the last instruction above.
        """

    except IOError as ex:
        print("Failed to get settings")
        ex_string = traceback.format_exc()
        print(ex_string)
    except (BNCAttention, BNCCritical) as ex:
        ex_string = traceback.format_exc()
        print(ex_string)
    except Exception as ex:
        print("Unknown EXCEPTION type raised")
        ex_string = traceback.format_exc()
        print(ex_string)
        account.logger.error(ex_string)      # TODO: temporarily, get clear output of unspecified exceptions
        # if price is not None:
        #    price.stop()
